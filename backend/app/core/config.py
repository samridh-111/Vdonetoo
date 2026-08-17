from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"

    # Supabase
    supabase_url: str
    supabase_service_role_key: str
    supabase_db_url: str
    supabase_audio_bucket: str = "ivr-audio"
    supabase_batch_bucket: str = "ivr-batches"

    # ElevenLabs
    elevenlabs_api_key: str
    elevenlabs_max_concurrency: int = 8
    elevenlabs_rate_per_min: int = 60
    elevenlabs_preview_text: str = (
        "Hello, this is a preview of this voice for Automation Hub."
    )

    # Translation
    translation_provider: Literal["openai", "gemini", "mymemory"] = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"
    # MyMemory needs no API key -- a free, keyless stand-in for demos while
    # OpenAI/Gemini billing gets sorted out (not a long-term replacement:
    # anonymous usage is capped around 5000 chars/day, ~50000/day if
    # mymemory_contact_email is set, per MyMemory's own terms).
    mymemory_contact_email: str = ""
    # A batch fans out one translation call per script concurrently, which
    # can burst past a low-tier account's requests-per-minute limit (seen
    # in practice with a free-trial OpenAI key exhausting the SDK's own
    # retries under 3 concurrent scripts). Kept conservative by default.
    translation_max_concurrency: int = 2
    translation_rate_per_min: int = 20

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Frontend (read here only so a single .env can drive both, unused by the API itself)
    next_public_api_url: str = "http://localhost:8000"
    next_public_ws_url: str = "ws://localhost:8000"
    # The deployed frontend's own origin, e.g. https://your-app.vercel.app --
    # added to CORS allow_origins for production. Distinct from
    # next_public_api_url above, which is the *backend's* URL and must never
    # be put in allow_origins (that was a real bug: CORS allow_origins needs
    # the caller's origin, not the API's own address).
    frontend_url: str = ""

    # Testing
    ivr_test_force_failures: int = Field(default=0)

    @property
    def has_live_keys(self) -> bool:
        if self.translation_provider == "openai":
            provider_ready = bool(self.openai_api_key)
        elif self.translation_provider == "gemini":
            provider_ready = bool(self.gemini_api_key)
        else:  # mymemory needs no key
            provider_ready = True
        return bool(self.elevenlabs_api_key and provider_ready and self.supabase_service_role_key)

    @property
    def cors_allow_origins(self) -> list[str]:
        # Next's dev server falls back to 3001, 3002, etc. whenever a lower
        # port is already taken (as happened in local dev here, where 3000
        # was occupied by an unrelated process) -- so every likely dev port
        # is allowed rather than hardcoding just 3000.
        origins = [f"http://localhost:{port}" for port in range(3000, 3005)]
        if self.frontend_url:
            origins.append(self.frontend_url)
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
