from app.domain.interfaces.repositories import LanguageRepository
from app.domain.interfaces.translation_provider import TranslationProvider


class TranslationService:
    """Resolves language codes to human-readable names (so provider adapters
    stay decoupled from the `languages` registry) and delegates the actual
    translation call to whichever provider the batch was configured with."""

    def __init__(self, language_repository: LanguageRepository) -> None:
        self._languages = language_repository

    async def translate(
        self,
        provider: TranslationProvider,
        text: str,
        source_language_code: str,
        target_language_code: str,
    ) -> str:
        source = await self._languages.get(source_language_code)
        target = await self._languages.get(target_language_code)
        source_name = source.name if source is not None else source_language_code
        target_name = target.name if target is not None else target_language_code
        return await provider.translate(text, source_name, target_name)
