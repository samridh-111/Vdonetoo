from typing import Protocol


class LanguageDetector(Protocol):
    """Contract for detecting the language of a script's text. Concrete
    implementation: app/providers/language/detector.py (langdetect + the
    `languages` table registry, so new languages are a data insert, not a
    code change)."""

    async def detect(self, text: str) -> str:
        """Returns a language code present in the `languages` table, falling
        back to 'en' if detection is inconclusive or unmapped."""
        ...
