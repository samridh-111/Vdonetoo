import uuid

import pytest

from app.domain.entities import VoiceEntity
from app.services.voice_service import VoiceResolutionService


def _make_voice(name: str, preset_key: str, language_code: str | None) -> VoiceEntity:
    return VoiceEntity(
        id=uuid.uuid4(),
        name=name,
        preset_key=preset_key,
        elevenlabs_voice_id=f"voice-{preset_key}",
        language_code=language_code,
        similarity=0.75,
        stability=0.5,
        style=0.0,
        speed=1.0,
        sample_audio_url=None,
        is_active=True,
        created_at=None,  # type: ignore[arg-type]
    )


class FakeVoiceRepository:
    def __init__(self, voices: list[VoiceEntity]) -> None:
        self._voices = voices

    async def list_active(self, language_code: str | None = None) -> list[VoiceEntity]:
        if language_code is None:
            return list(self._voices)
        return [v for v in self._voices if v.language_code == language_code]

    async def get(self, voice_id: uuid.UUID) -> VoiceEntity | None:
        return next((v for v in self._voices if v.id == voice_id), None)

    async def get_by_preset_key(self, preset_key: str) -> VoiceEntity | None:
        return next((v for v in self._voices if v.preset_key == preset_key), None)

    async def first_active_for_language(self, language_code: str) -> VoiceEntity | None:
        return next((v for v in self._voices if v.language_code == language_code), None)

    async def get_fallback(self) -> VoiceEntity | None:
        return await self.get_by_preset_key("professional")


@pytest.fixture
def voices() -> list[VoiceEntity]:
    return [
        _make_voice("Professional", "professional", None),
        _make_voice("Vedantu Female", "vedantu_female", None),
        _make_voice("Teacher Female", "teacher_female", "hi"),
    ]


async def test_resolve_uses_explicit_voice_hint(voices: list[VoiceEntity]) -> None:
    service = VoiceResolutionService(FakeVoiceRepository(voices))  # type: ignore[arg-type]

    resolved = await service.resolve(voice_hint="Vedantu Female", default_voice_map={}, language_code="en")

    assert resolved is not None
    assert resolved.preset_key == "vedantu_female"


async def test_resolve_falls_back_to_batch_default_voice_map(voices: list[VoiceEntity]) -> None:
    service = VoiceResolutionService(FakeVoiceRepository(voices))  # type: ignore[arg-type]

    resolved = await service.resolve(
        voice_hint=None, default_voice_map={"en": "vedantu_female"}, language_code="en"
    )

    assert resolved is not None
    assert resolved.preset_key == "vedantu_female"


async def test_resolve_falls_back_to_first_active_for_language(voices: list[VoiceEntity]) -> None:
    service = VoiceResolutionService(FakeVoiceRepository(voices))  # type: ignore[arg-type]

    resolved = await service.resolve(voice_hint=None, default_voice_map={}, language_code="hi")

    assert resolved is not None
    assert resolved.preset_key == "teacher_female"


async def test_resolve_falls_back_to_professional_preset(voices: list[VoiceEntity]) -> None:
    service = VoiceResolutionService(FakeVoiceRepository(voices))  # type: ignore[arg-type]

    resolved = await service.resolve(voice_hint=None, default_voice_map={}, language_code="ta")

    assert resolved is not None
    assert resolved.preset_key == "professional"


async def test_resolve_hint_is_fuzzy_matched_by_name(voices: list[VoiceEntity]) -> None:
    service = VoiceResolutionService(FakeVoiceRepository(voices))  # type: ignore[arg-type]

    resolved = await service.resolve(voice_hint="vedantu female voice", default_voice_map={}, language_code="en")

    assert resolved is not None
    assert resolved.preset_key == "vedantu_female"
