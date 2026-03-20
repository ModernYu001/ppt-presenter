# Build Plan — Windows MVP

## Phase 1 — Project Skeleton
- [x] Create project structure
- [x] Write PRD and architecture
- [ ] Initialize Electron app
- [ ] Initialize Python backend

## Phase 2 — Backend Foundations
- [ ] Config persistence
- [ ] OpenAI-compatible model discovery
- [ ] Chat completion wrapper
- [ ] PPT parser using `python-pptx`
- [ ] Windows PowerPoint COM controller
- [ ] Presentation orchestrator state machine

## Phase 3 — Voice Pipeline
- [ ] Voice sample import/record endpoint
- [ ] Clone backend abstraction
- [ ] TTS backend abstraction
- [ ] Playback pipeline

## Phase 4 — Desktop UI
- [ ] Settings screen
- [ ] Voice setup screen
- [ ] PPT loader
- [ ] Live presentation console
- [ ] Logs/status panel

## Phase 5 — Real-Time Presentation
- [ ] Slide change polling
- [ ] Narration generation cache
- [ ] Next-slide prefetch
- [ ] Pause/resume/replay/next controls

## Phase 6 — Packaging
- [ ] Windows run instructions
- [ ] Installer strategy
- [ ] Env/config export

## Suggested First Coding Milestone

Build a local backend that can:
1. store URL/Key/model
2. call `/v1/models`
3. parse a `.pptx`
4. return slide summaries as JSON

Then attach Electron UI to that backend.
