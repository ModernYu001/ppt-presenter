from pydantic import BaseModel, Field


class ConfigRequest(BaseModel):
    base_url: str = Field(default="")
    api_key: str = Field(default="")
    model: str = Field(default="")
    voice_profile: str = Field(default="")
    tts_provider: str = Field(default="local")
    elevenlabs_api_key: str = Field(default="")
    elevenlabs_voice_id: str = Field(default="")
    elevenlabs_model_id: str = Field(default="eleven_multilingual_v2")


class ModelDiscoveryRequest(BaseModel):
    base_url: str
    api_key: str = Field(default="")


class PptLoadRequest(BaseModel):
    path: str


class NarrationRequest(BaseModel):
    slide_index: int
    text: str = Field(default="")
    notes: str = Field(default="")
    style: str = Field(default="professional")
    duration_hint_sec: int = Field(default=45)


class OpenPptRequest(BaseModel):
    path: str


class PresentationControlRequest(BaseModel):
    path: str | None = None


class SpeakRequest(BaseModel):
    text: str
    voice_id: str = Field(default="")
    rate: int = Field(default=185)
    volume: float = Field(default=1.0)


class ElevenLabsSpeakRequest(BaseModel):
    text: str
    api_key: str = Field(default="")
    voice_id: str = Field(default="")
    model_id: str = Field(default="eleven_multilingual_v2")


class ElevenLabsCreateVoiceRequest(BaseModel):
    name: str
    description: str = Field(default="")
    sample_paths: list[str] = Field(default_factory=list)
    api_key: str = Field(default="")
