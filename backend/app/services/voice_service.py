import uuid

from rapidfuzz import fuzz, process

from app.domain.entities import VoiceEntity
from app.domain.interfaces.repositories import VoiceRepository
from app.domain.interfaces.voice_provider import VoiceProvider

_FUZZY_MATCH_THRESHOLD = 80


class VoiceResolutionService:
    """Resolves which voice a job should use, in priority order: the
    script's own Voice column -> the batch's default_voice_map for that
    language -> the first active voice registered for that language -> the
    'Professional' fallback preset."""

    def __init__(self, voice_repository: VoiceRepository) -> None:
        self._voices = voice_repository

    async def resolve(
        self,
        *,
        voice_hint: str | None,
        default_voice_map: dict[str, str],
        language_code: str,
    ) -> VoiceEntity | None:
        if voice_hint:
            matched = await self._match_hint(voice_hint)
            if matched is not None:
                return matched

        mapped_reference = default_voice_map.get(language_code)
        if mapped_reference:
            matched = await self._resolve_reference(mapped_reference)
            if matched is not None:
                return matched

        matched = await self._voices.first_active_for_language(language_code)
        if matched is not None:
            return matched

        return await self._voices.get_fallback()

    async def _match_hint(self, hint: str) -> VoiceEntity | None:
        preset_key = hint.strip().lower().replace(" ", "_")
        voice = await self._voices.get_by_preset_key(preset_key)
        if voice is not None:
            return voice

        candidates = await self._voices.list_active()
        if not candidates:
            return None
        by_name = {voice.name.lower(): voice for voice in candidates}
        best = process.extractOne(
            hint.lower(), list(by_name.keys()), scorer=fuzz.WRatio, score_cutoff=_FUZZY_MATCH_THRESHOLD
        )
        return by_name[best[0]] if best else None

    async def _resolve_reference(self, reference: str) -> VoiceEntity | None:
        voice = await self._voices.get_by_preset_key(reference)
        if voice is not None:
            return voice
        try:
            voice_id = uuid.UUID(reference)
        except ValueError:
            return None
        return await self._voices.get(voice_id)

    async def generate_preview(self, voice: VoiceEntity, provider: VoiceProvider, preview_text: str) -> bytes:
        return await provider.generate_speech(
            preview_text,
            voice.elevenlabs_voice_id,
            stability=voice.stability,
            similarity=voice.similarity,
            style=voice.style,
            speed=voice.speed,
        )
