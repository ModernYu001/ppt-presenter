# Electron App (One-Click Run)

## Dev mode (with auto backend)

```bash
cd electron
npm install
npm run dev
```

The Electron main process will auto-start the backend using:
- `python3` by default
- script: `../python/run_backend.py`

Override if needed:

```bash
export PYTHON_BIN=/path/to/python
export BACKEND_SCRIPT=/absolute/path/to/run_backend.py
```

## Production build

```bash
npm run build
npm run start
```
