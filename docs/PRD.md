# PRD — PPT Auto Presenter (Windows MVP)

## 1. Goal

Build a local Windows desktop application that can open a PPT, understand each slide, generate spoken narration from a user-configured online model endpoint, and present the deck in real time with a cloned user voice.

## 2. Primary User Story

As a presenter, I want to point the app to my PowerPoint file, configure my model endpoint and API key, record my voice once, and let the system present the slides automatically in my speaking style.

## 3. MVP Requirements

### 3.1 Model Configuration
- Input `Base URL`
- Input `API Key`
- Fetch model list from `GET /v1/models`
- Allow selecting an available model from the fetched list
- Persist configuration locally

### 3.2 Voice Setup
- First-run voice sample recording/import
- Store voice profile metadata locally
- Abstract voice clone provider behind interface
- Allow testing a sample sentence before presentation

### 3.3 PPT Selection and Parsing
- Choose a single `.pptx` file
- Optional directory mode for future multi-file support
- Parse slide title, body, notes, and basic structure
- Optional screenshot pipeline reserved for later visual understanding

### 3.4 Presentation Flow
- Open PPT in Microsoft PowerPoint on Windows
- Start slideshow mode
- Detect current slide index
- Generate narration for the current slide using configured model
- Play TTS audio for the narration
- Prefetch narration for the next slide
- Support pause/resume/next/replay

### 3.5 Logging and Diagnostics
- Surface backend logs in UI
- Show current slide number and state
- Show model request status and errors
- Show TTS generation/playback state

## 4. Non-Goals for MVP

- Mac/Linux support
- Full audience Q&A
- Multi-speaker voice profiles
- Perfect image/chart understanding
- Plugin installation inside PowerPoint

## 5. Functional Components

1. Desktop UI
2. Settings storage
3. Model registry client
4. PowerPoint controller
5. Slide parser
6. Narration planner
7. TTS / voice clone adapter
8. Presentation orchestrator
9. Local API server

## 6. UX Screens

- Home dashboard
- Model settings
- Voice setup
- PPT selection
- Live presentation console
- Logs / diagnostics drawer

## 7. Risks

- PowerPoint COM automation reliability differs by Office version
- Voice clone quality depends heavily on selected backend
- Real-time generation latency must be hidden with prefetch/cache
- Some slides are image-heavy and need future visual parsing

## 8. MVP Success Criteria

- User can configure a model endpoint
- App can fetch and select a model from the configured URL
- App can open a PPT and detect active slide
- App can generate and speak slide narration with low-friction controls
- Presenter can finish a deck with the tool acting as auto-speaker
