import json
from pathlib import Path


class ConfigService:
    def __init__(self) -> None:
        self.config_path = Path(__file__).resolve().parents[2] / "data" / "config.json"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.config_path.exists():
            return {
                "base_url": "",
                "api_key": "",
                "model": "",
                "voice_profile": "",
                "tts_provider": "local",
                "elevenlabs_api_key": "",
                "elevenlabs_voice_id": "",
                "elevenlabs_model_id": "eleven_multilingual_v2",
            }
        data = json.loads(self.config_path.read_text(encoding="utf-8"))
        defaults = {
            "base_url": "",
            "api_key": "",
            "model": "",
            "voice_profile": "",
            "tts_provider": "local",
            "elevenlabs_api_key": "",
            "elevenlabs_voice_id": "",
            "elevenlabs_model_id": "eleven_multilingual_v2",
        }
        defaults.update(data)
        return defaults

    def save(self, payload: dict):
        self.config_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
