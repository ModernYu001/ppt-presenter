class VoiceProvider:
    """Abstraction for voice cloning / TTS backends."""

    def create_profile(self, sample_path: str) -> str:
        raise NotImplementedError

    def synthesize(self, text: str, voice_profile: str) -> str:
        raise NotImplementedError
