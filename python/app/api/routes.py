from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ConfigRequest,
    ElevenLabsCreateVoiceRequest,
    ElevenLabsSpeakRequest,
    ModelDiscoveryRequest,
    NarrationRequest,
    OpenPptRequest,
    PptLoadRequest,
    SpeakRequest,
)
from app.services.config_service import ConfigService
from app.services.model_service import ModelService
from app.services.narration_service import NarrationService
from app.services.ppt_service import PptService
from app.services.presentation_service import PresentationService
from app.services.tts_service import TtsService

router = APIRouter(prefix="/api")
config_service = ConfigService()
model_service = ModelService(config_service)
ppt_service = PptService()
tts_service = TtsService(config_service)
narration_service = NarrationService(config_service, model_service, ppt_service, tts_service)
presentation_service = PresentationService()


@router.get("/config")
def get_config():
    return config_service.load()


@router.post("/config")
def save_config(payload: ConfigRequest):
    config_service.save(payload.model_dump())
    return {"ok": True}


@router.post("/models/discover")
async def discover_models(payload: ModelDiscoveryRequest):
    try:
        models = await model_service.discover_models(payload.base_url, payload.api_key)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"models": models}


@router.post("/narration/generate")
async def generate_narration(payload: NarrationRequest):
    try:
        text = await model_service.generate_narration(
            slide_index=payload.slide_index,
            text=payload.text,
            notes=payload.notes,
            style=payload.style,
            duration_hint_sec=payload.duration_hint_sec,
        )
        presentation_service.set_last_narration(payload.slide_index, text)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"text": text}


@router.post("/tts/speak")
def speak_text(payload: SpeakRequest):
    try:
        result = tts_service.speak(payload.text, voice_id=payload.voice_id or None, rate=payload.rate, volume=payload.volume)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result


@router.get("/tts/voices")
def list_voices():
    try:
        voices = tts_service.available_voices()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"voices": voices}


@router.get("/tts/elevenlabs/voices")
async def list_elevenlabs_voices():
    config = config_service.load()
    api_key = config.get("elevenlabs_api_key", "")
    try:
        voices = await tts_service.elevenlabs_list_voices(api_key)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"voices": voices}


@router.post("/tts/elevenlabs/create-voice")
async def create_elevenlabs_voice(payload: ElevenLabsCreateVoiceRequest):
    config = config_service.load()
    api_key = payload.api_key or config.get("elevenlabs_api_key", "")
    try:
        result = await tts_service.elevenlabs_create_voice(
            api_key=api_key,
            name=payload.name,
            sample_paths=payload.sample_paths,
            description=payload.description,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    voice_id = result.get("voice_id", "")
    if voice_id:
        config["elevenlabs_voice_id"] = voice_id
        config_service.save(config)
    return result


@router.post("/tts/elevenlabs/speak")
async def elevenlabs_speak(payload: ElevenLabsSpeakRequest):
    config = config_service.load()
    api_key = payload.api_key or config.get("elevenlabs_api_key", "")
    voice_id = payload.voice_id or config.get("elevenlabs_voice_id", "")
    model_id = payload.model_id or config.get("elevenlabs_model_id", "eleven_multilingual_v2")
    try:
        result = await tts_service.elevenlabs_speak(
            text=payload.text,
            api_key=api_key,
            voice_id=voice_id,
            model_id=model_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result


@router.post("/ppt/load")
def load_ppt(payload: PptLoadRequest):
    try:
        slides = ppt_service.load_presentation(payload.path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"slides": slides}


@router.post("/ppt/open")
def open_ppt(payload: OpenPptRequest):
    try:
        state = presentation_service.open_ppt(payload.path)
        narration_service.prefetch_slide(payload.path, 1)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return state


@router.post("/presentation/start")
def start_presentation():
    try:
        state = presentation_service.start_slideshow()
        deck_path = state.get("deck_path")
        current_slide = state.get("current_slide") or 1
        if deck_path:
            narration_service.prefetch_slide(deck_path, int(current_slide))
            narration_service.prefetch_slide(deck_path, int(current_slide) + 1)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return state


@router.post("/presentation/next")
def next_slide():
    try:
        state = presentation_service.next_slide()
        deck_path = state.get("deck_path")
        current_slide = state.get("current_slide")
        if deck_path and current_slide:
            presentation_service.mark_slide_unspoken(int(current_slide))
            narration_service.prefetch_slide(deck_path, int(current_slide))
            narration_service.prefetch_slide(deck_path, int(current_slide) + 1)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return state


@router.post("/presentation/previous")
def previous_slide():
    try:
        state = presentation_service.previous_slide()
        current_slide = state.get("current_slide")
        deck_path = state.get("deck_path")
        if current_slide:
            presentation_service.mark_slide_unspoken(int(current_slide))
        if deck_path and current_slide:
            narration_service.prefetch_slide(deck_path, int(current_slide))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return state


@router.post("/presentation/auto-start")
def auto_start():
    state = presentation_service.get_state()
    deck_path = state.get("deck_path")
    if not deck_path:
        raise HTTPException(status_code=400, detail="No deck_path in presentation state; open a PPT first")

    def runner(slide_index: int):
        result = narration_service.speak_slide(deck_path, slide_index)
        presentation_service.set_last_narration(slide_index, result["narration"])

    try:
        current_slide = state.get("current_slide") or 1
        narration_service.prefetch_slide(deck_path, int(current_slide))
        narration_service.prefetch_slide(deck_path, int(current_slide) + 1)
        state = presentation_service.start_auto_mode(runner)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return state


@router.post("/presentation/auto-stop")
def auto_stop():
    try:
        state = presentation_service.stop_auto_mode()
        tts_service.stop()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return state


@router.get("/presentation/cache")
def presentation_cache():
    state = presentation_service.get_state()
    deck_path = state.get("deck_path")
    if not deck_path:
        return {"cached_slides": []}
    return narration_service.cache_status(deck_path)


@router.get("/presentation/state")
def presentation_state():
    return presentation_service.get_state()
