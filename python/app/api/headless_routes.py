"""Headless presenter API: upload PPTX → async process → download MP4.

Endpoints:
    POST   /api/headless/upload    → upload .pptx, returns job_id
    GET    /api/headless/status/{job_id}  → job progress
    GET    /api/headless/download/{job_id} → download finished MP4
    GET    /api/headless/jobs      → list recent jobs
    DELETE /api/headless/jobs/{job_id}  → delete job
"""

from __future__ import annotations

import os
import shutil
import threading
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Header
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/headless")

# --- Config ---
UPLOAD_DIR = Path(os.getenv("HEADLESS_UPLOAD_DIR", "/home/ec2-user/.openclaw/workspace/ppt-auto-presenter/data/uploads"))
OUTPUT_DIR = Path(os.getenv("HEADLESS_OUTPUT_DIR", "/home/ec2-user/.openclaw/workspace/ppt-auto-presenter/data/outputs"))
AUTH_TOKEN = os.getenv("HEADLESS_AUTH_TOKEN", "ppt-presenter-2026")
MAX_FILE_SIZE_MB = int(os.getenv("HEADLESS_MAX_FILE_MB", "50"))

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --- In-memory job store ---
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


def _check_auth(authorization: str | None):
    if not AUTH_TOKEN:
        return
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")


def _get_job(job_id: str) -> dict:
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


def _update_job(job_id: str, **kwargs):
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id].update(kwargs)


def _run_headless(job_id: str, pptx_path: str, voice: str):
    """Background worker: run headless_present pipeline."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

    try:
        _update_job(job_id, status="parsing", progress=5)

        from headless_present import parse_pptx, render_slide_image, generate_narration, generate_tts, stitch_video, get_audio_duration
        import asyncio

        workdir = OUTPUT_DIR / job_id / "work"
        workdir.mkdir(parents=True, exist_ok=True)
        out_path = str(OUTPUT_DIR / job_id / "presentation.mp4")

        # Step 1: Parse
        slides = parse_pptx(pptx_path)
        total = len(slides)
        _update_job(job_id, status="rendering", progress=10, total_slides=total)

        # Step 2: Render images
        for slide in slides:
            img_path = str(workdir / f"slide_{slide['index']:03d}.png")
            render_slide_image(slide, img_path)
            slide["image"] = img_path
            pct = 10 + int(20 * slide["index"] / total)
            _update_job(job_id, progress=pct, current_step=f"rendered slide {slide['index']}/{total}")

        # Step 3: Narration
        _update_job(job_id, status="narrating", progress=30)
        for slide in slides:
            try:
                slide["narration"] = generate_narration(slide)
            except Exception:
                slide["narration"] = slide.get("text") or f"第{slide['index']}页"
            pct = 30 + int(30 * slide["index"] / total)
            _update_job(job_id, progress=pct, current_step=f"narration slide {slide['index']}/{total}")

        # Step 4: TTS
        _update_job(job_id, status="synthesizing", progress=60)
        for slide in slides:
            audio_path = str(workdir / f"slide_{slide['index']:03d}.mp3")
            asyncio.run(generate_tts(slide["narration"], audio_path, voice=voice))
            slide["audio"] = audio_path
            pct = 60 + int(25 * slide["index"] / total)
            _update_job(job_id, progress=pct, current_step=f"tts slide {slide['index']}/{total}")

        # Step 5: Stitch
        _update_job(job_id, status="stitching", progress=85, current_step="composing video")
        stitch_video(slides, out_path)

        if os.path.exists(out_path):
            size_mb = os.path.getsize(out_path) / (1024 * 1024)
            _update_job(
                job_id,
                status="done",
                progress=100,
                current_step="complete",
                output_path=out_path,
                output_size_mb=round(size_mb, 2),
                completed_at=time.time(),
            )
        else:
            _update_job(job_id, status="failed", progress=100, error="Video file not created")

    except Exception as e:
        _update_job(job_id, status="failed", progress=100, error=str(e))


# --- Routes ---

@router.post("/upload")
async def upload_pptx(
    file: UploadFile = File(...),
    authorization: str | None = Header(None),
    voice: str = "zh-CN-XiaoxiaoNeural",
):
    _check_auth(authorization)

    if not file.filename or not file.filename.lower().endswith(".pptx"):
        raise HTTPException(status_code=400, detail="Only .pptx files are accepted")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"File too large ({size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB limit)")

    job_id = str(uuid.uuid4())[:12]
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    pptx_path = str(job_dir / file.filename)

    with open(pptx_path, "wb") as f:
        f.write(content)

    job = {
        "job_id": job_id,
        "filename": file.filename,
        "size_mb": round(size_mb, 2),
        "voice": voice,
        "status": "queued",
        "progress": 0,
        "total_slides": 0,
        "current_step": "",
        "error": "",
        "output_path": "",
        "output_size_mb": 0,
        "created_at": time.time(),
        "completed_at": None,
    }

    with _jobs_lock:
        _jobs[job_id] = job

    thread = threading.Thread(target=_run_headless, args=(job_id, pptx_path, voice), daemon=True)
    thread.start()

    return {"job_id": job_id, "status": "queued", "filename": file.filename}


@router.get("/status/{job_id}")
def job_status(job_id: str, authorization: str | None = Header(None)):
    _check_auth(authorization)
    job = _get_job(job_id)
    return {k: v for k, v in job.items() if k != "output_path"}


@router.get("/download/{job_id}")
def download_video(job_id: str, authorization: str | None = Header(None)):
    _check_auth(authorization)
    job = _get_job(job_id)
    if job["status"] != "done":
        raise HTTPException(status_code=400, detail=f"Job not ready: {job['status']}")
    path = job.get("output_path", "")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Output file not found")
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=f"{job.get('filename', 'presentation').replace('.pptx', '')}.mp4",
    )


@router.get("/jobs")
def list_jobs(authorization: str | None = Header(None)):
    _check_auth(authorization)
    with _jobs_lock:
        items = sorted(_jobs.values(), key=lambda x: x.get("created_at", 0), reverse=True)
    return {"jobs": [{k: v for k, v in j.items() if k != "output_path"} for j in items[:20]]}


@router.delete("/jobs/{job_id}")
def delete_job(job_id: str, authorization: str | None = Header(None)):
    _check_auth(authorization)
    with _jobs_lock:
        job = _jobs.pop(job_id, None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # Cleanup files
    for d in [UPLOAD_DIR / job_id, OUTPUT_DIR / job_id]:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
    return {"ok": True, "deleted": job_id}
