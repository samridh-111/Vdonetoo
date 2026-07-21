from typing import Protocol


class TranslationProvider(Protocol):
    """Provider-agnostic translation contract. Concrete implementations:
    app/providers/translation/{openai_provider,gemini_provider}.py, selected
    at runtime via app/providers/translation/factory.py.

    `source_language`/`target_language` are human-readable names (e.g.
    "English", "Hindi"), not codes -- the caller (translation_service.py)
    resolves codes to names via the `languages` registry so providers stay
    decoupled from that registry and work for any language name."""

    async def translate(self, text: str, source_language: str, target_language: str) -> str: ...
