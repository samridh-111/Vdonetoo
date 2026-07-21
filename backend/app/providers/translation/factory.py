from functools import lru_cache
from typing import Literal

from app.core.config import get_settings
from app.domain.interfaces.translation_provider import TranslationProvider
from app.providers.translation.gemini_provider import GeminiTranslationProvider
from app.providers.translation.openai_provider import OpenAITranslationProvider


@lru_cache
def get_translation_provider(name: Literal["openai", "gemini"]) -> TranslationProvider:
    """One provider instance per provider name, reused across requests/tasks
    within a process. `name` normally comes from `batches.translation_provider`
    (chosen per-batch), falling back to `settings.translation_provider`."""
    settings = get_settings()

    if name == "openai":
        return OpenAITranslationProvider(api_key=settings.openai_api_key, model=settings.openai_model)
    if name == "gemini":
        return GeminiTranslationProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)

    raise ValueError(f"Unknown translation provider: {name}")
