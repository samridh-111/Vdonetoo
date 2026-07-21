"""Builders for services/providers used inside Celery tasks. Centralized here
so every task file constructs them the same way, and so `worker_process_init`
(app/core/celery_app.py) has one place to clear process-local singletons
after a prefork fork."""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.providers.language.detector import LangDetectLanguageDetector
from app.providers.storage.supabase_storage import SupabaseStorageProvider
from app.providers.translation.factory import get_translation_provider
from app.providers.voice.elevenlabs_provider import ElevenLabsVoiceProvider
from app.repositories import (
    SqlAudioFileRepository,
    SqlBatchRepository,
    SqlJobRepository,
    SqlLanguageRepository,
    SqlLogRepository,
    SqlScriptRepository,
    SqlVoiceRepository,
)
from app.services.language_detection_service import LanguageDetectionService
from app.services.translation_service import TranslationService
from app.services.voice_service import VoiceResolutionService
from app.services.zip_service import ZipService


@lru_cache
def get_storage_provider() -> SupabaseStorageProvider:
    settings = get_settings()
    return SupabaseStorageProvider(settings.supabase_url, settings.supabase_service_role_key)


@lru_cache
def get_voice_provider() -> ElevenLabsVoiceProvider:
    settings = get_settings()
    return ElevenLabsVoiceProvider(settings.elevenlabs_api_key)


def build_language_detection_service(session: AsyncSession) -> LanguageDetectionService:
    language_repo = SqlLanguageRepository(session)
    detector = LangDetectLanguageDetector(language_repo)
    return LanguageDetectionService(detector, language_repo)


def build_translation_service(session: AsyncSession) -> TranslationService:
    return TranslationService(SqlLanguageRepository(session))


def build_voice_resolution_service(session: AsyncSession) -> VoiceResolutionService:
    return VoiceResolutionService(SqlVoiceRepository(session))


def build_zip_service(session: AsyncSession) -> ZipService:
    settings = get_settings()
    return ZipService(
        batch_repository=SqlBatchRepository(session),
        script_repository=SqlScriptRepository(session),
        job_repository=SqlJobRepository(session),
        audio_file_repository=SqlAudioFileRepository(session),
        log_repository=SqlLogRepository(session),
        voice_repository=SqlVoiceRepository(session),
        storage_provider=get_storage_provider(),
        audio_bucket=settings.supabase_audio_bucket,
        batch_bucket=settings.supabase_batch_bucket,
    )


__all__ = [
    "get_storage_provider",
    "get_voice_provider",
    "get_translation_provider",
    "build_language_detection_service",
    "build_translation_service",
    "build_voice_resolution_service",
    "build_zip_service",
]
