import uuid
from datetime import UTC, datetime

from celery import chord

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.core.db import new_worker_session
from app.core.rate_limiter import refill
from app.core.redis_client import get_sync_redis
from app.repositories import SqlBatchRepository, SqlJobRepository, SqlLogRepository, SqlScriptRepository
from app.workers.cancellation import is_batch_cancelled
from app.workers.factories import build_zip_service
from app.workers.loop import run_async
from app.workers.progress import publish_progress
from app.workers.tasks.audio_tasks import generate_audio_for_job
from app.workers.tasks.script_tasks import prepare_script


@celery_app.task(name="app.workers.tasks.pipeline_tasks.refill_rate_limit_tokens")
def refill_rate_limit_tokens() -> None:
    """Scheduled every second by celery-beat (see core/celery_app.py
    beat_schedule) to top up every rate-limited bucket (ElevenLabs,
    translation)."""
    settings = get_settings()
    redis_client = get_sync_redis()
    refill(redis_client, "elevenlabs", settings.elevenlabs_max_concurrency, settings.elevenlabs_rate_per_min)
    refill(redis_client, "translation", settings.translation_max_concurrency, settings.translation_rate_per_min)


@celery_app.task(name="app.workers.tasks.pipeline_tasks.orchestrate_batch")
def orchestrate_batch(batch_id: str) -> None:
    run_async(_orchestrate_batch_async(batch_id))


async def _orchestrate_batch_async(batch_id: str) -> None:
    batch_uuid = uuid.UUID(batch_id)

    async with new_worker_session() as session:
        batch_repo = SqlBatchRepository(session)
        script_repo = SqlScriptRepository(session)

        batch = await batch_repo.get(batch_uuid)
        if batch is None:
            return

        await batch_repo.update(batch_uuid, status="processing", started_at=datetime.now(UTC))
        scripts = await script_repo.list_by_batch(batch_uuid)

    publish_progress(batch_uuid, "batch_progress", {"stage": "preparing", "total_scripts": len(scripts)})

    pending_script_ids = [str(script.id) for script in scripts if script.status != "failed"]

    if not pending_script_ids or is_batch_cancelled(batch_uuid):
        dispatch_audio_generation.delay(batch_id)
        return

    chord((prepare_script.s(script_id) for script_id in pending_script_ids), dispatch_audio_generation.si(batch_id))()


@celery_app.task(name="app.workers.tasks.pipeline_tasks.dispatch_audio_generation")
def dispatch_audio_generation(batch_id: str) -> None:
    run_async(_dispatch_audio_generation_async(batch_id))


async def _dispatch_audio_generation_async(batch_id: str) -> None:
    batch_uuid = uuid.UUID(batch_id)

    async with new_worker_session() as session:
        batch_repo = SqlBatchRepository(session)
        job_repo = SqlJobRepository(session)

        # total_jobs must count every job (including ones prepare_script
        # already marked 'failed' for a translation error), not just the
        # ones still queued for audio generation -- otherwise batch stats
        # (percent complete, ZIP summary.json) undercount whenever any
        # translation failed.
        all_jobs = await job_repo.list_by_batch(batch_uuid)
        queued_jobs = [job for job in all_jobs if job.stage == "queued"]
        await batch_repo.update(batch_uuid, total_jobs=len(all_jobs))

    publish_progress(batch_uuid, "batch_progress", {"stage": "generating", "total_jobs": len(all_jobs)})

    cancelled = is_batch_cancelled(batch_uuid)
    if cancelled:
        async with new_worker_session() as session:
            await SqlBatchRepository(session).update(batch_uuid, status="cancelled", completed_at=datetime.now(UTC))
        publish_progress(batch_uuid, "batch_cancelled", {"reason": "Batch cancelled."})
        return

    if not all_jobs:
        async with new_worker_session() as session:
            await SqlBatchRepository(session).update(batch_uuid, status="failed", completed_at=datetime.now(UTC))
        publish_progress(batch_uuid, "batch_failed", {"reason": "No jobs could be prepared."})
        return

    if not queued_jobs:
        # Every job already failed translation before reaching audio
        # generation -- still build the ZIP so metadata.csv/logs.txt
        # document what happened, rather than aborting silently.
        build_zip_and_finalize.delay(batch_id)
        return

    job_ids = [str(job.id) for job in queued_jobs]
    chord((generate_audio_for_job.s(job_id) for job_id in job_ids), build_zip_and_finalize.si(batch_id))()


@celery_app.task(name="app.workers.tasks.pipeline_tasks.build_zip_and_finalize")
def build_zip_and_finalize(batch_id: str) -> None:
    run_async(_build_zip_and_finalize_async(batch_id))


async def _build_zip_and_finalize_async(batch_id: str) -> None:
    batch_uuid = uuid.UUID(batch_id)

    async with new_worker_session() as session:
        batch_repo = SqlBatchRepository(session)
        log_repo = SqlLogRepository(session)

        # DB is the source of truth for final counts, not the incrementally
        # maintained batch.completed_jobs/failed_jobs counters or the raw
        # chord result list.
        completed_count, failed_count = await batch_repo.recompute_job_counts(batch_uuid)
        batch = await batch_repo.get(batch_uuid)
        total_jobs = batch.total_jobs if batch else 0
        final_status = "failed" if total_jobs > 0 and failed_count == total_jobs else "completed"

        # Build the ZIP *before* flipping the batch to a terminal status --
        # otherwise there's a window where the frontend sees status
        # 'completed' (and shows the Download button) while
        # zip_storage_path is still null, producing "This batch's ZIP
        # isn't ready yet" on a click that looks like it should work.
        zip_path: str | None = None
        try:
            zip_service = build_zip_service(session)
            zip_path = await zip_service.build_and_upload(batch_uuid)
        except Exception as exc:  # noqa: BLE001 -- a ZIP build failure must not mask the batch's real completion status
            await log_repo.create(batch_uuid, f"ZIP build failed: {exc}", level="error")

        await batch_repo.update(
            batch_uuid,
            completed_jobs=completed_count,
            failed_jobs=failed_count,
            status=final_status,
            completed_at=datetime.now(UTC),
            zip_storage_path=zip_path,
        )

    publish_progress(
        batch_uuid,
        "batch_completed" if final_status == "completed" else "batch_failed",
        {
            "completed_jobs": completed_count,
            "failed_jobs": failed_count,
            "total_jobs": total_jobs,
            "zip_ready": zip_path is not None,
        },
    )
