# Electron Packaging (electron-builder)

## Requirements

- Node.js 18+
- npm
- Python backend already in `../python`

### Windows build host

- Windows machine
- Optional: bundled Python runtime
- Optional: prebuilt `ppt-backend.exe`

### macOS build host

- macOS machine
- `python3` available on `PATH`, or set `PYTHON_RUNTIME_DIR` to a macOS Python runtime/venv to bundle
- Microsoft PowerPoint or another `.pptx`-capable app installed if you want `Open PPTX` to launch the deck locally

## Build Windows installer

```bash
cd electron
npm install
npm run dist
```

Produces an NSIS installer in `./dist-app/`.

## Build macOS DMG

```bash
cd electron
npm install
npm run dist:mac
```

Produces a DMG in `./dist-app/`.

Electron Builder should produce the DMG on macOS.

## Runtime behavior by platform

- Windows: opens PowerPoint through COM and enables start-show, next-slide, and auto-present controls.
- macOS: opens the `.pptx` with the system `open` command and leaves slideshow control disabled in the UI because COM automation is not available.
- Other platforms: PowerPoint integration is not supported.

## Notes

- The backend (`../python`) is bundled into the app via `files` in `package.json`.
- The app auto-starts the backend using a bundled Python runtime when present; otherwise it falls back to `python3`.

### Bundle Python runtime (optional)

Set `PYTHON_RUNTIME_DIR` before running the packaging command.

Windows example:

```bash
set PYTHON_RUNTIME_DIR=C:\\python-embed
npm run dist
```

macOS example:

```bash
export PYTHON_RUNTIME_DIR=/Library/Frameworks/Python.framework/Versions/3.11
npm run dist:mac
```

The runtime will be copied into `electron/python-runtime/` and packaged into the app.

For Windows builds, you can use the official embeddable zip from:
- https://www.python.org/downloads/windows/

### Bundle backend exe (optional, Windows only)

If you have a prebuilt backend executable, place it in a folder and set:

```bash
set BACKEND_EXE_DIR=C:\\backend-exe
npm run dist
```

The app will prefer `backend-exe/ppt-backend.exe` at runtime.
You can also override with `BACKEND_EXE` env var.
