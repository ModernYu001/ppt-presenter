from __future__ import annotations

import asyncio
import threading
from pathlib import Path

from app.services.model_service import ModelService
from app.services.ppt_service import PptService
from app.services.tts_service import TtsService


class NarrationService:
    def __init__(self, config_service, model_service: ModelService, ppt_service: PptService, tts_service: TtsService):
        self.config_service = config_service
        self.model_service = model_service
        self.ppt_service = ppt_service
        self.tts_service = tts_service
        self._slide_cache = {}
        self._narration_cache = {}
        self._prefetch_threads = {}

    def _load_slides(self, path: str):
        path = str(Path(path))
        if path not in self._slide_cache:
            self._slide_cache[path] = self.ppt_service.load_presentation(path)
        return self._slide_cache[path]

    def get_slide(self, path: str, slide_index: int):
        slides = self._load_slides(path)
        for slide in slides:
            if int(slide["index"]) == int(slide_index):
                return slide
        raise ValueError(f"Slide {slide_index} not found")

    def _cache_key(self, path: str, slide_index: int):
        return f"{Path(path)}::{slide_index}"

    async def generate_for_slide(self, path: str, slide_index: int, use_cache: bool = True):
        key = self._cache_key(path, slide_index)
        if use_cache and key in self._narration_cache:
            return self._narration_cache[key]

        slide = self.get_slide(path, slide_index)
        text = await self.model_service.generate_narration(
            slide_index=slide_index,
            text=slide.get("text", ""),
            notes=slide.get("notes", ""),
            style="professional",
            duration_hint_sec=45,
        )
        result = {"slide": slide, "narration": text}
        self._narration_cache[key] = result
        return result

    def generate_for_slide_sync(self, path: str, slide_index: int, use_cache: bool = True):
        return asyncio.run(self.generate_for_slide(path, slide_index, use_cache=use_cache))

    def speak_slide(self, path: str, slide_index: int):
        result = self.generate_for_slide_sync(path, slide_index, use_cache=True)
        self.tts_service.speak_with_config(result["narration"])
        self.prefetch_slide(path, slide_index + 1)
        return result

    def prefetch_slide(self, path: str, slide_index: int):
        try:
            self.get_slide(path, slide_index)
        except Exception:
            return {"ok": True, "prefetched": False, "reason": "slide_not_found"}

        key = self._cache_key(path, slide_index)
        if key in self._narration_cache:
            return {"ok": True, "prefetched": True, "cached": True}

        if key in self._prefetch_threads and self._prefetch_threads[key].is_alive():
            return {"ok": True, "prefetched": False, "reason": "already_running"}

        def worker():
            try:
                self.generate_for_slide_sync(path, slide_index, use_cache=True)
            except Exception:
                pass

        thread = threading.Thread(target=worker, daemon=True)
        self._prefetch_threads[key] = thread
        thread.start()
        return {"ok": True, "prefetched": True, "cached": False}

    def cache_status(self, path: str):
        prefix = f"{Path(path)}::"
        cached = [k for k in self._narration_cache.keys() if k.startswith(prefix)]
        return {"cached_slides": sorted(cached)}
