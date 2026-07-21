from elevenlabs import VoiceSettings
from elevenlabs.client import AsyncElevenLabs

_MODEL_ID = "eleven_multilingual_v2"  # supports all 10 target languages from any premade voice


class ElevenLabsVoiceProvider:
    def __init__(self, api_key: str) -> None:
        self._client = AsyncElevenLabs(api_key=api_key)

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
        audio_chunks = self._client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id=_MODEL_ID,
            voice_settings=VoiceSettings(
                stability=stability,
                similarity_boost=similarity,
                style=style,
                speed=speed,
                use_speaker_boost=True,
            ),
        )
        chunks = bytearray()
        async for chunk in audio_chunks:
            chunks.extend(chunk)
        return bytes(chunks)
