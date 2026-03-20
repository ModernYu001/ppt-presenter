from __future__ import annotations

import asyncio
import os
import sys
import threading
from pathlib import Path

from app.integrations.elevenlabs_provider import ElevenLabsProvider


class TtsService:
    """Simple local TTS wrapper plus ElevenLabs provider support."""

    def __init__(self, config_service=None):
        self.config_service = config_service
        self._engine = None
        self._lock = threading.Lock()
        self.elevenlabs = ElevenLabsProvider()
        self._audio_cache_dir = Path(__file__).resolve().parents[2] / "data" / "audio"
        self._audio_cache_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_engine(self):
        if self._engine is not None:
            return self._engine
        try:
            import pyttsx3
        except Exception as exc:
            raise RuntimeError("pyttsx3 is not installed; run pip install -r requirements.txt") from exc
        self._engine = pyttsx3.init()
        return self._engine

    def available_voices(self):
        engine = self._ensure_engine()
        voices = []
        for v in engine.getProperty("voices"):
            voices.append(
                {
                    "id": getattr(v, "id", ""),
                    "name": getattr(v, "name", ""),
                    "languages": [str(x) for x in getattr(v, "languages", [])],
                }
            )
        return voices

    def speak(self, text: str, voice_id: str | None = None, rate: int = 185, volume: float = 1.0):
        if not text.strip():
            return {"ok": True, "spoken": False}
        with self._lock:
            engine = self._ensure_engine()
            engine.setProperty("rate", rate)
            engine.setProperty("volume", volume)
            if voice_id:
                try:
                    engine.setProperty("voice", voice_id)
                except Exception:
                    pass
            engine.say(text)
            engine.runAndWait()
        return {"ok": True, "spoken": True, "provider": "local"}

    async def elevenlabs_list_voices(self, api_key: str):
        return await self.elevenlabs.list_voices(api_key)

    async def elevenlabs_create_voice(self, api_key: str, name: str, sample_paths: list[str], description: str = ""):
        return await self.elevenlabs.create_voice(api_key=api_key, name=name, files=sample_paths, description=description)

    async def elevenlabs_speak(self, text: str, api_key: str, voice_id: str, model_id: str = "eleven_multilingual_v2"):
        audio_bytes = await self.elevenlabs.synthesize(api_key=api_key, voice_id=voice_id, text=text, model_id=model_id)
        out_path = self._audio_cache_dir / "elevenlabs_latest.mp3"
        self.elevenlabs.save_audio(audio_bytes, str(out_path))
        self._play_audio_file(str(out_path))
        return {"ok": True, "spoken": True, "provider": "elevenlabs", "path": str(out_path)}

    def _play_audio_file(self, path: str):
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                import subprocess
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.Popen([opener, path])
        except Exception as exc:
            raise RuntimeError(f"Failed to play audio file: {exc}") from exc

    def speak_with_config(self, text: str):
        config = self.config_service.load() if self.config_service else {}
        provider = config.get("tts_provider", "local")
        if provider == "elevenlabs":
            return asyncio.run(
                self.elevenlabs_speak(
                    text=text,
                    api_key=config.get("elevenlabs_api_key", ""),
                    voice_id=config.get("elevenlabs_voice_id", ""),
                    model_id=config.get("elevenlabs_model_id", "eleven_multilingual_v2"),
                )
            )
        return self.speak(
            text=text,
            voice_id=config.get("voice_profile") or None,
            rate=185,
            volume=1.0,
        )

    def stop(self):
        with self._lock:
            if self._engine is not None:
                self._engine.stop()
        return {"ok": True}
