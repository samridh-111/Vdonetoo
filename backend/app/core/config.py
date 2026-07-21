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
    translation_provider: Literal["openai", "gemini"] = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Frontend (read here only so a single .env can drive both, unused by the API itself)
    next_public_api_url: str = "http://localhost:8000"
    next_public_ws_url: str = "ws://localhost:8000"

    # Testing
    ivr_test_force_failures: int = Field(default=0)

    @property
    def has_live_keys(self) -> bool:
        provider_key = (
            self.openai_api_key if self.translation_provider == "openai" else self.gemini_api_key
        )
        return bool(self.elevenlabs_api_key and provider_key and self.supabase_service_role_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
