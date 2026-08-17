from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.db import get_db_session
from app.core.redis_client import get_redis
from app.domain.interfaces.voice_provider import VoiceProvider
from app.providers.language.detector import LangDetectLanguageDetector
from app.repositories import (
    SqlAudioFileRepository,
    SqlBatchRepository,
    SqlJobRepository,
    SqlLanguageRepository,
    SqlLogRepository,
    SqlProjectRepository,
    SqlScriptRepository,
    SqlTranslationRepository,
    SqlUserRepository,
    SqlVoiceRepository,
)
from app.services.batch_service import BatchService
from app.services.language_detection_service import LanguageDetectionService
from app.services.pipeline_orchestrator import PipelineOrchestrator
from app.services.upload_service import UploadService
from app.services.voice_service import VoiceResolutionService
from app.workers.factories import get_storage_provider, get_voice_provider

SettingsDep = Annotated[Settings, Depends(get_settings)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


async def get_async_redis() -> AsyncIterator[Redis]:
    yield get_redis()


RedisDep = Annotated[Redis, Depends(get_async_redis)]


def get_project_repository(session: DbSessionDep) -> SqlProjectRepository:
    return SqlProjectRepository(session)


def get_batch_repository(session: DbSessionDep) -> SqlBatchRepository:
    return SqlBatchRepository(session)


def get_script_repository(session: DbSessionDep) -> SqlScriptRepository:
    return SqlScriptRepository(session)


def get_job_repository(session: DbSessionDep) -> SqlJobRepository:
    return SqlJobRepository(session)


def get_audio_file_repository(session: DbSessionDep) -> SqlAudioFileRepository:
    return SqlAudioFileRepository(session)


def get_language_repository(session: DbSessionDep) -> SqlLanguageRepository:
    return SqlLanguageRepository(session)


def get_voice_repository(session: DbSessionDep) -> SqlVoiceRepository:
    return SqlVoiceRepository(session)


def get_translation_repository(session: DbSessionDep) -> SqlTranslationRepository:
    return SqlTranslationRepository(session)


def get_log_repository(session: DbSessionDep) -> SqlLogRepository:
    return SqlLogRepository(session)


def get_user_repository(session: DbSessionDep) -> SqlUserRepository:
    return SqlUserRepository(session)


def get_upload_service() -> UploadService:
    return UploadService()


def get_language_detection_service(
    language_repository: Annotated[SqlLanguageRepository, Depends(get_language_repository)],
) -> LanguageDetectionService:
    detector = LangDetectLanguageDetector(language_repository)
    return LanguageDetectionService(detector, language_repository)


def get_voice_resolution_service(
    voice_repository: Annotated[SqlVoiceRepository, Depends(get_voice_repository)],
) -> VoiceResolutionService:
    return VoiceResolutionService(voice_repository)


def get_pipeline_orchestrator() -> PipelineOrchestrator:
    from app.core.redis_client import get_sync_redis

    return PipelineOrchestrator(get_sync_redis())


def get_batch_service(
    project_repository: Annotated[SqlProjectRepository, Depends(get_project_repository)],
    batch_repository: Annotated[SqlBatchRepository, Depends(get_batch_repository)],
    script_repository: Annotated[SqlScriptRepository, Depends(get_script_repository)],
    job_repository: Annotated[SqlJobRepository, Depends(get_job_repository)],
    audio_file_repository: Annotated[SqlAudioFileRepository, Depends(get_audio_file_repository)],
    upload_service: Annotated[UploadService, Depends(get_upload_service)],
    orchestrator: Annotated[PipelineOrchestrator, Depends(get_pipeline_orchestrator)],
    settings: SettingsDep,
) -> BatchService:
    return BatchService(
        project_repository=project_repository,
        batch_repository=batch_repository,
        script_repository=script_repository,
        job_repository=job_repository,
        audio_file_repository=audio_file_repository,
        upload_service=upload_service,
        orchestrator=orchestrator,
        storage_provider=get_storage_provider(),
        batch_bucket=settings.supabase_batch_bucket,
        default_translation_provider=settings.translation_provider,
        elevenlabs_max_concurrency=settings.elevenlabs_max_concurrency,
    )


def get_elevenlabs_provider() -> VoiceProvider:
    return get_voice_provider()
