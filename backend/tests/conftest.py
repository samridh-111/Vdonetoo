import os

import pytest

# Settings has several required fields with no defaults (real credentials
# are expected in production/.env). Unit tests that never actually call the
# external services just need *some* value present so Settings() doesn't
# raise on import; integration tests that need real keys check
# settings.has_live_keys themselves and skip if they're still these dummies.
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("SUPABASE_DB_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres")
os.environ.setdefault("ELEVENLABS_API_KEY", "test-elevenlabs-key")
os.environ.setdefault("ENVIRONMENT", "test")


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    from app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
