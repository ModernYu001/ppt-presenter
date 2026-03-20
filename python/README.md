# Python Backend

## Run locally

```bash
cd python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_backend.py
```

Backend starts at `http://127.0.0.1:18765`.

## Platform behavior

- Windows: `.pptx` parsing, narration generation, TTS, and PowerPoint slideshow control are supported when Microsoft PowerPoint is installed.
- macOS: `.pptx` parsing, narration generation, TTS, and `open`-based deck launching are supported, but slideshow start/navigation/auto-present remain disabled because COM is Windows-only.
- Linux and other platforms: `.pptx` parsing, narration generation, and TTS work; PowerPoint integration is unsupported.

## Build backend exe (Windows)

```powershell
cd python
powershell -ExecutionPolicy Bypass -File build_backend_exe.ps1
```

This will produce:

```
python/dist/ppt-backend.exe
```

Copy the exe to a folder and set `BACKEND_EXE_DIR` when building the Electron installer.

## Current capabilities

- save/load local config
- discover models from `GET /v1/models`
- parse `.pptx` slide text and notes
- generate narration from configured OpenAI-compatible endpoint
- Windows PowerPoint COM control scaffold with open/start/next/current-slide methods
- macOS `.pptx` launch path using the system `open` command

## Notes

- PowerPoint COM actions only work on Windows with Microsoft PowerPoint installed.
- On macOS, `POST /api/ppt/open` launches the deck with `open`, but the backend reports `supports_slideshow_control=false` so the desktop app can disable slideshow automation.
- ElevenLabs audio playback uses `open` on macOS and `xdg-open` on Linux.
