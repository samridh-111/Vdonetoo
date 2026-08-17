import pytest

from app.core.config import get_settings
from app.providers.translation.factory import get_translation_provider
from app.providers.translation.gemini_provider import GeminiTranslationProvider
from app.providers.translation.mymemory_provider import MyMemoryTranslationProvider
from app.providers.translation.openai_provider import OpenAITranslationProvider


@pytest.fixture(autouse=True)
def _clear_provider_cache():
    get_translation_provider.cache_clear()
    yield
    get_translation_provider.cache_clear()


def test_factory_returns_openai_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()

    provider = get_translation_provider("openai")

    assert isinstance(provider, OpenAITranslationProvider)


def test_factory_returns_gemini_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    get_settings.cache_clear()

    provider = get_translation_provider("gemini")

    assert isinstance(provider, GeminiTranslationProvider)


def test_factory_returns_mymemory_provider() -> None:
    get_settings.cache_clear()

    provider = get_translation_provider("mymemory")

    assert isinstance(provider, MyMemoryTranslationProvider)


def test_factory_caches_provider_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()

    first = get_translation_provider("openai")
    second = get_translation_provider("openai")

    assert first is second


def test_factory_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError):
        get_translation_provider("anthropic")  # type: ignore[arg-type]
