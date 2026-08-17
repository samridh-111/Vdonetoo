import io
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from mutagen.mp3 import MP3

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.core.db import new_worker_session
from app.core.rate_limiter import try_acquire
from app.core.redis_client import get_sync_redis
from app.repositories import (
    SqlAudioFileRepository,
    SqlBatchRepository,
    SqlJobRepository,
    SqlLogRepository,
    SqlScriptRepository,
    SqlTranslationRepository,
    SqlVoiceRepository,
)
from app.workers.cancellation import is_batch_cancelled
from app.workers.factories import get_storage_provider, get_voice_provider
from app.workers.loop import run_async
from app.workers.progress import publish_progress

RATE_LIMIT_RETRY_COUNTDOWN = 2
FAILURE_RETRY_COUNTDOWN = 5


class _RetryableJobError(Exception):
    """Raised internally to signal the sync wrapper should call self.retry();
    never allowed to escape the task itself."""


@celery_app.task(
    name="app.workers.tasks.audio_tasks.generate_audio_for_job",
    bind=True,
    max_retries=None,  # uncapped at the Celery level -- see module docstring below
)
def generate_audio_for_job(self: Any, job_id: str) -> dict[str, Any]:
    """Two independent retry paths, both using Celery's self.retry() for the
    re-queue mechanism but governed by different, uncoupled counters:

    1. Rate-limit waits (bucket empty) retry indefinitely -- this is normal
       backpressure, not a failure, and must never count against a job's
       3-attempt failure budget.
    2. Genuine failures (ElevenLabs error, upload error) are capped at 3
       attempts, tracked via the `jobs.attempt`/`jobs.max_attempts` DB
       columns (not Celery's own retry counter, which the rate-limit path
       above also increments). On the 4th failure the job is marked
       'failed' and this function returns a result dict instead of
       raising -- that's what guarantees the batch-wide chord callback
       still fires and the rest of the batch keeps going.
    """
    settings = get_settings()
    if not try_acquire(get_sync_redis(), "elevenlabs", settings.elevenlabs_max_concurrency):
        raise self.retry(countdown=RATE_LIMIT_RETRY_COUNTDOWN)

    try:
        return run_async(_generate_audio_async(job_id))
    except _RetryableJobError as exc:
        raise self.retry(exc=exc.__cause__ or exc, countdown=FAILURE_RETRY_COUNTDOWN) from exc


async def _generate_audio_async(job_id: str) -> dict[str, Any]:
    job_uuid = uuid.UUID(job_id)
    settings = get_settings()

    async with new_worker_session() as session:
        job_repo = SqlJobRepository(session)
        script_repo = SqlScriptRepository(session)
        translation_repo = SqlTranslationRepository(session)
        voice_repo = SqlVoiceRepository(session)
        batch_repo = SqlBatchRepository(session)
        audio_file_repo = SqlAudioFileRepository(session)
        log_repo = SqlLogRepository(session)

        job = await job_repo.get(job_uuid)
        if job is None or job.stage in ("completed", "failed"):
            return {"job_id": job_id, "status": "skipped"}

        if is_batch_cancelled(job.batch_id):
            await job_repo.update(job_uuid, stage="failed", error_message="Batch cancelled")
            await batch_repo.increment_counters(job.batch_id, failed_delta=1)
            return {"job_id": job_id, "status": "cancelled"}

        script = await script_repo.get(job.script_id)
        translation = await translation_repo.get(job.translation_id) if job.translation_id else None
        voice = await voice_repo.get(job.voice_id) if job.voice_id else None

        if script is None or translation is None or translation.translated_text is None or voice is None:
            await job_repo.update(
                job_uuid, stage="failed", error_message="Missing script, translation, or voice for this job."
            )
            await batch_repo.increment_counters(job.batch_id, failed_delta=1)
            await log_repo.create(
                job.batch_id, f"Job {job_id} failed: missing prerequisite data.", level="error", job_id=job_uuid
            )
            publish_progress(job.batch_id, "job_stage_changed", {"job_id": job_id, "status": "failed"})
            return {"job_id": job_id, "status": "failed"}

        attempt = job.attempt + 1
        await job_repo.update(
            job_uuid,
            stage="generating",
            attempt=attempt,
            started_at=job.started_at or datetime.now(UTC),
        )
        publish_progress(job.batch_id, "job_stage_changed", {"job_id": job_id, "status": "generating"})

        try:
            voice_provider = get_voice_provider()
            start = time.perf_counter()
            audio_bytes = await voice_provider.generate_speech(
                translation.translated_text,
                voice.elevenlabs_voice_id,
                stability=voice.stability,
                similarity=voice.similarity,
                style=voice.style,
                speed=voice.speed,
            )
            generation_time_ms = int((time.perf_counter() - start) * 1000)

            await job_repo.update(job_uuid, stage="uploading")
            publish_progress(job.batch_id, "job_stage_changed", {"job_id": job_id, "status": "uploading"})

            storage_path = f"batches/{job.batch_id}/{job.language_code}/{job_id}.mp3"
            storage_provider = get_storage_provider()
            await storage_provider.upload(settings.supabase_audio_bucket, storage_path, audio_bytes, "audio/mpeg")

            duration_seconds = _read_mp3_duration(audio_bytes)

            await audio_file_repo.create(
                job_id=job_uuid,
                script_id=job.script_id,
                batch_id=job.batch_id,
                language_code=job.language_code,
                voice_id=job.voice_id,
                storage_path=storage_path,
                duration_seconds=duration_seconds,
                file_size_bytes=len(audio_bytes),
                generation_time_ms=generation_time_ms,
            )
            await job_repo.update(job_uuid, stage="completed", completed_at=datetime.now(UTC))
            await batch_repo.increment_counters(job.batch_id, completed_delta=1)
            publish_progress(job.batch_id, "job_stage_changed", {"job_id": job_id, "status": "completed"})
            return {"job_id": job_id, "status": "completed"}

        except Exception as exc:  # noqa: BLE001 -- must classify every failure into retry-vs-terminal, never propagate raw
            if attempt < job.max_attempts:
                await job_repo.update(job_uuid, stage="retrying")
                await log_repo.create(
                    job.batch_id,
                    f"Job {job_id} attempt {attempt}/{job.max_attempts} failed, will retry: {exc}",
                    level="warning",
                    job_id=job_uuid,
                )
                publish_progress(job.batch_id, "job_stage_changed", {"job_id": job_id, "status": "retrying"})
                raise _RetryableJobError(str(exc)) from exc

            await job_repo.update(
                job_uuid, stage="failed", error_message=str(exc), completed_at=datetime.now(UTC)
            )
            await batch_repo.increment_counters(job.batch_id, failed_delta=1)
            await log_repo.create(
                job.batch_id,
                f"Job {job_id} failed permanently after {job.max_attempts} attempts: {exc}",
                level="error",
                job_id=job_uuid,
            )
            publish_progress(job.batch_id, "job_stage_changed", {"job_id": job_id, "status": "failed"})
            return {"job_id": job_id, "status": "failed", "error": str(exc)}


def _read_mp3_duration(audio_bytes: bytes) -> float | None:
    try:
        info = MP3(io.BytesIO(audio_bytes)).info  # type: ignore[no-untyped-call]
        return float(info.length) if info is not None else None
    except Exception:  # noqa: BLE001 -- duration is best-effort metadata, never worth failing the job over
        return None
