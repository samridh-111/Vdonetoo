import pytest

from app.domain.entities import LanguageEntity
from app.providers.language.detector import LangDetectLanguageDetector
from app.services.language_detection_service import LanguageDetectionService

_LANGUAGES: dict[str, LanguageEntity] = {
    "en": LanguageEntity(code="en", name="English", locale="en-IN", detector_aliases=["en"], header_synonyms=["english"]),
    "hi": LanguageEntity(code="hi", name="Hindi", locale="hi-IN", detector_aliases=["hi"], header_synonyms=["hindi"]),
    "ta": LanguageEntity(code="ta", name="Tamil", locale="ta-IN", detector_aliases=["ta"], header_synonyms=["tamil"]),
}


class FakeLanguageRepository:
    async def list_active(self) -> list[LanguageEntity]:
        return list(_LANGUAGES.values())

    async def get(self, code: str) -> LanguageEntity | None:
        return _LANGUAGES.get(code)

    async def resolve_detector_alias(self, alias: str) -> LanguageEntity | None:
        for language in _LANGUAGES.values():
            if alias.lower() in language.detector_aliases:
                return language
        return None

    async def resolve_header_synonym(self, token: str) -> LanguageEntity | None:
        normalized = token.strip().lower()
        for language in _LANGUAGES.values():
            if normalized in language.header_synonyms:
                return language
        return None


class FakeDetector:
    def __init__(self, forced_code: str) -> None:
        self.forced_code = forced_code
        self.calls = 0

    async def detect(self, text: str) -> str:
        self.calls += 1
        return self.forced_code


@pytest.fixture
def language_repository() -> FakeLanguageRepository:
    return FakeLanguageRepository()


async def test_resolve_prefers_explicit_hint_over_detection(language_repository: FakeLanguageRepository) -> None:
    detector = FakeDetector(forced_code="en")
    service = LanguageDetectionService(detector, language_repository)  # type: ignore[arg-type]

    result = await service.resolve("some script text", language_hint="Hindi")

    assert result == "hi"
    assert detector.calls == 0  # hint resolved successfully, detector never invoked


async def test_resolve_falls_back_to_detector_when_no_hint(language_repository: FakeLanguageRepository) -> None:
    detector = FakeDetector(forced_code="ta")
    service = LanguageDetectionService(detector, language_repository)  # type: ignore[arg-type]

    result = await service.resolve("some script text", language_hint=None)

    assert result == "ta"
    assert detector.calls == 1


async def test_resolve_falls_back_to_detector_when_hint_unmapped(language_repository: FakeLanguageRepository) -> None:
    detector = FakeDetector(forced_code="en")
    service = LanguageDetectionService(detector, language_repository)  # type: ignore[arg-type]

    result = await service.resolve("some script text", language_hint="Klingon")

    assert result == "en"
    assert detector.calls == 1


@pytest.mark.parametrize(
    ("text", "expected_alias"),
    [
        ("Welcome to our support center, how can I help you today?", "en"),
        ("नमस्ते, आपका हमारे सहायता केंद्र में स्वागत है", "hi"),
    ],
)
async def test_real_langdetect_maps_through_registry(
    language_repository: FakeLanguageRepository, text: str, expected_alias: str
) -> None:
    detector = LangDetectLanguageDetector(language_repository)  # type: ignore[arg-type]
    result = await detector.detect(text)
    assert result == expected_alias


async def test_real_langdetect_falls_back_on_empty_text(language_repository: FakeLanguageRepository) -> None:
    detector = LangDetectLanguageDetector(language_repository)  # type: ignore[arg-type]
    result = await detector.detect("   ")
    assert result == "en"
