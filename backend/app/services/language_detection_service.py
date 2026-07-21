from app.domain.interfaces.language_detector import LanguageDetector
from app.domain.interfaces.repositories import LanguageRepository


class LanguageDetectionService:
    """Resolves the language of a script: an explicit Language-column hint
    takes priority (resolved through the `languages.header_synonyms`
    registry); otherwise falls back to running the language detector against
    the script text itself."""

    def __init__(self, detector: LanguageDetector, language_repository: LanguageRepository) -> None:
        self._detector = detector
        self._languages = language_repository

    async def resolve(self, script_text: str, language_hint: str | None) -> str:
        if language_hint:
            language = await self._languages.resolve_header_synonym(language_hint)
            if language is not None:
                return language.code

        return await self._detector.detect(script_text)
