from typing import Protocol


class VoiceProvider(Protocol):
    """Contract for text-to-speech generation. Concrete implementation:
    app/providers/voice/elevenlabs_provider.py."""

    async def generate_speech(
        self,
        text: str,
        voice_id: str,
        *,
        stability: float,
        similarity: float,
        style: float,
        speed: float,
    ) -> bytes:
        """Returns raw mp3 bytes."""
        ...
