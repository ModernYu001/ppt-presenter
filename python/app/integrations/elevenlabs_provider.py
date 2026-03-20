from __future__ import annotations

from pathlib import Path

import httpx


class ElevenLabsProvider:
    base_url = "https://api.elevenlabs.io/v1"

    async def list_voices(self, api_key: str):
        headers = {"xi-api-key": api_key}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}/voices", headers=headers)
            response.raise_for_status()
            data = response.json()
        return data.get("voices", [])

    async def synthesize(self, api_key: str, voice_id: str, text: str, model_id: str = "eleven_multilingual_v2"):
        if not api_key:
            raise ValueError("Missing ElevenLabs API key")
        if not voice_id:
            raise ValueError("Missing ElevenLabs voice_id")
        payload = {
            "text": text,
            "model_id": model_id,
        }
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.base_url}/text-to-speech/{voice_id}", headers=headers, json=payload)
            response.raise_for_status()
            audio_bytes = response.content
        return audio_bytes

    async def create_voice(self, api_key: str, name: str, files: list[str], description: str = ""):
        if not api_key:
            raise ValueError("Missing ElevenLabs API key")
        if not name:
            raise ValueError("Missing voice name")
        if not files:
            raise ValueError("No sample files provided")

        headers = {"xi-api-key": api_key}
        data = {
            "name": name,
            "description": description,
        }
        multipart = []
        opened = []
        try:
            for file_path in files:
                path = Path(file_path)
                fh = path.open("rb")
                opened.append(fh)
                multipart.append(("files", (path.name, fh, "audio/mpeg")))
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(f"{self.base_url}/voices/add", headers=headers, data=data, files=multipart)
                response.raise_for_status()
                return response.json()
        finally:
            for fh in opened:
                try:
                    fh.close()
                except Exception:
                    pass

    def save_audio(self, audio_bytes: bytes, out_path: str):
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(audio_bytes)
        return str(path)
