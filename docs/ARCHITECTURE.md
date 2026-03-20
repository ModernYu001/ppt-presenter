# Architecture — PPT Auto Presenter

## Overview

The system is split into a Windows desktop shell and a local Python backend.

```text
Electron UI
  ├─ Settings / Controls / Logs
  ├─ Calls local backend HTTP API
  └─ Renders presentation state

Python Backend (FastAPI)
  ├─ Model Client
  │   ├─ GET /v1/models
  │   └─ POST /v1/chat/completions
  ├─ PPT Parser
  │   └─ python-pptx
  ├─ PowerPoint Controller
  │   └─ win32com (Windows only)
  ├─ Narration Engine
  │   ├─ Prompt builder
  │   ├─ Slide cache
  │   └─ Next-slide prefetch
  ├─ Voice Service
  │   ├─ Voice sample intake
  │   ├─ Clone profile abstraction
  │   └─ TTS synthesis abstraction
  └─ Orchestrator
      ├─ Slide change detection
      ├─ Playback control
      └─ State machine
```

## Data Flow

1. User configures Base URL + API Key + Model.
2. Backend fetches models from remote endpoint.
3. User selects PPT.
4. Backend parses deck and stores slide metadata.
5. User starts presentation.
6. PowerPoint slideshow starts.
7. On current slide:
   - collect slide text + notes
   - build narration prompt
   - request model output
   - synthesize/play speech
8. Prefetch next slide narration in parallel.

## Core Services

### 1. Config Service
Persists local app settings, active endpoint, active model, and voice profile.

### 2. Model Service
OpenAI-compatible wrapper around:
- `GET /v1/models`
- `POST /v1/chat/completions`

### 3. PPT Service
- Parse `.pptx` with `python-pptx`
- Normalize slide content into a compact internal schema

### 4. PowerPoint Runtime Service
- Open and control slide show using COM
- Observe active slide index
- Trigger on-slide-enter events via polling for MVP

### 5. Voice Service
- Save recorded/imported samples
- Create voice profile via pluggable backend
- Generate playable audio from narration text

### 6. Orchestrator Service
State machine:
- `idle`
- `ready`
- `presenting`
- `paused`
- `error`

## API Surface (Local)

### Config
- `GET /api/config`
- `POST /api/config`
- `POST /api/models/discover`

### Voice
- `POST /api/voice/sample`
- `POST /api/voice/clone`
- `POST /api/voice/test`

### PPT
- `POST /api/ppt/load`
- `GET /api/ppt/slides`
- `POST /api/ppt/open`
- `POST /api/ppt/start`

### Presentation
- `POST /api/presentation/start`
- `POST /api/presentation/pause`
- `POST /api/presentation/resume`
- `POST /api/presentation/replay`
- `POST /api/presentation/next`
- `GET /api/presentation/state`

## Recommended MVP Stack

### Desktop
- Electron
- React or plain HTML/JS for renderer
- electron-store or JSON file persistence

### Backend
- Python 3.11+
- FastAPI
- Uvicorn
- httpx
- python-pptx
- pywin32
- pydantic
- simpleaudio / pygame / provider-specific player

## Packaging Direction

- Electron build for Windows installer
- Python backend bundled or installed with embedded runtime later
- First milestone can run backend separately for faster iteration
