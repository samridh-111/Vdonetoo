import pytest

from app.providers.translation.mymemory_provider import MyMemoryTranslationProvider


async def test_rejects_unmapped_target_language() -> None:
    provider = MyMemoryTranslationProvider()

    with pytest.raises(ValueError, match="no ISO mapping"):
        await provider.translate("hello", "English", "Klingon")
