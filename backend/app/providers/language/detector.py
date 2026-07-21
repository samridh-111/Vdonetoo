from langdetect import DetectorFactory, LangDetectException, detect

from app.core.logging import get_logger
from app.domain.interfaces.repositories import LanguageRepository

# langdetect's detection is non-deterministic across runs unless seeded.
DetectorFactory.seed = 0

logger = get_logger(__name__)

_FALLBACK_LANGUAGE_CODE = "en"


class LangDetectLanguageDetector:
    """Wraps `langdetect` (pure Python, no large model download -- adequate
    given the 10 target languages use visually distinct scripts) and maps its
    output through the `languages` table registry, so supporting a new
    language later is a data insert, not a code change."""

    def __init__(self, language_repository: LanguageRepository) -> None:
        self._languages = language_repository

    async def detect(self, text: str) -> str:
        stripped = text.strip()
        if not stripped:
            return _FALLBACK_LANGUAGE_CODE

        try:
            raw_code = detect(stripped)
        except LangDetectException:
            logger.warning("language_detection_failed", text_preview=stripped[:50])
            return _FALLBACK_LANGUAGE_CODE

        language = await self._languages.resolve_detector_alias(raw_code)
        if language is None:
            logger.warning("language_detection_unmapped", raw_code=raw_code, text_preview=stripped[:50])
            return _FALLBACK_LANGUAGE_CODE

        return language.code
