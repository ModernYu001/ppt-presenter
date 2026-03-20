# PPT Auto Presenter

A Windows-first (now macOS-capable) local desktop tool that opens PPTX files, generates slide-by-slide narration using a configurable OpenAI-compatible model endpoint, and presents the deck with voice output.

> **Status:** Core workflow is implemented and UI is now a React + Tailwind console. Packaging support (electron-builder) and one-click run are in place. macOS support is added for opening PPTX and narration, but slide show control remains Windows-only.

---

## Features

### ✅ Implemented
- **Model endpoint config**: Base URL, API key, model selection via `GET /v1/models`
- **Narration generation**: `POST /v1/chat/completions` per slide
- **PPTX parsing**: slide text + notes extraction
- **Auto narration loop** (Windows): slide change → generate → speak
- **TTS providers**: local TTS + ElevenLabs (speak + clone entry)
- **React console UI** (dark, modern layout)
- **Electron auto-start backend**
- **Packaging**: electron-builder config + optional Python runtime bundling
- **Backend EXE option**: use PyInstaller for `ppt-backend.exe`

### ⚠️ In Progress / Next
- End-to-end real machine validation on macOS/Windows
- UI polish & workflow ergonomics
- Windows installer bundling with embedded Python runtime (optional)

---

## Architecture

```
/electron   -> Electron shell + React UI
/python     -> FastAPI backend (PPT control, model calls, narration, TTS)
/docs       -> PRD / architecture notes / plans
```

---

## Quick Start (Dev)

### 1) Backend
```bash
cd python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_backend.py
```

### 2) Frontend
```bash
cd electron
npm install
npm run dev
```

---

## One-click run
Electron main process auto-starts the backend. Default command:
- `python3 ../python/run_backend.py`

Override if needed:
```bash
export PYTHON_BIN=/path/to/python
export BACKEND_SCRIPT=/absolute/path/to/run_backend.py
```

---

## Packaging (Windows)

```bash
cd electron
npm install
npm run dist
```

Output: `electron/dist-app/`

### Optional: bundle Python runtime
```bash
set PYTHON_RUNTIME_DIR=C:\python-embed
npm run dist
```

### Optional: bundle backend EXE
```bash
set BACKEND_EXE_DIR=C:\backend-exe
npm run dist
```

---

## macOS Support (Current)

### ✅ What works on macOS
- PPTX parsing
- Model discovery + narration generation
- TTS playback (opens audio via `open`)
- PPTX **open** using macOS `open` command

### ❌ What does not (yet)
- PowerPoint slideshow control (COM is Windows-only)
- Auto-present controls (disabled on macOS)

The UI shows a macOS note and disables slideshow controls automatically.

---

## macOS Plan (Next Steps)

1. **Native PPT control**
   - Integrate `osascript` (AppleScript) to control PowerPoint on macOS.
   - If PowerPoint is unavailable, fallback to Keynote or open-only mode.

2. **Slide tracking**
   - Use AppleScript to query current slide index during slideshow.

3. **Auto-present enablement**
   - Re-enable auto-present once slide index can be read on macOS.

4. **Packaging**
   - Build `.dmg` via `npm run dist:mac` (already configured)

---

## Repo structure (key files)

- `electron/src/renderer/ui/App.jsx` → UI
- `python/app/services/` → core backend services
- `python/app/integrations/powerpoint_com.py` → Windows/macOS PPT opening logic

---

## License
MIT (placeholder — update if needed)
