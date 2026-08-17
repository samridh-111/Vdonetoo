import uuid
from dataclasses import asdict

from redis.asyncio import Redis

from app.domain.entities import BatchEntity, JobEntity
from app.domain.interfaces.repositories import (
    AudioFileRepository,
    BatchRepository,
    JobRepository,
    ProjectRepository,
    ScriptRepository,
)
from app.domain.interfaces.storage_provider import StorageProvider
from app.schemas.batch import BatchCreateRequest, BatchDetail, BatchEstimateResponse, BatchStatusOut
from app.schemas.script import JobOut, ScriptOut
from app.services.pipeline_orchestrator import PipelineOrchestrator
from app.services.upload_service import UploadService

_DEFAULT_PROJECT_NAME = "IVR Automation"
_DEFAULT_PROJECT_MODULE = "ivr_automation"

# Used only until enough real jobs have completed to compute a historical
# average -- roughly matches translate + TTS + upload latency observed in
# practice, not a fabricated number pretending to be measured data (the
# response's `based_on_historical_data` flag tells the caller which one it got).
_FALLBACK_MS_PER_JOB = 4000.0


class BatchNotFoundError(Exception):
    pass


class BatchStateError(Exception):
    pass


class BatchService:
    def __init__(
        self,
        project_repository: ProjectRepository,
        batch_repository: BatchRepository,
        script_repository: ScriptRepository,
        job_repository: JobRepository,
        audio_file_repository: AudioFileRepository,
        upload_service: UploadService,
        orchestrator: PipelineOrchestrator,
        storage_provider: StorageProvider,
        batch_bucket: str,
        default_translation_provider: str,
        elevenlabs_max_concurrency: int,
    ) -> None:
        self._projects = project_repository
        self._batches = batch_repository
        self._scripts = script_repository
        self._jobs = job_repository
        self._audio_files = audio_file_repository
        self._upload_service = upload_service
        self._orchestrator = orchestrator
        self._storage = storage_provider
        self._batch_bucket = batch_bucket
        self._default_translation_provider = default_translation_provider
        self._elevenlabs_max_concurrency = elevenlabs_max_concurrency

    async def create_batch(self, redis: Redis, request: BatchCreateRequest) -> BatchEntity:
        stash = await self._upload_service.unstash(redis, request.upload_token)
        rows = stash.rows

        project = await self._projects.get_or_create_default(_DEFAULT_PROJECT_MODULE, _DEFAULT_PROJECT_NAME)

        batch = await self._batches.create(
            project_id=project.id,
            name=request.name,
            source_type=stash.source_type,
            source_filename=stash.source_filename,
            source_url=stash.source_url,
            translation_mode=request.translation_mode.value,
            target_languages=request.target_languages,
            translation_provider=(
                request.translation_provider.value
                if request.translation_provider is not None
                else self._default_translation_provider
            ),
            default_voice_map=request.default_voice_map,
            status="draft",
            concurrency_limit=request.concurrency_limit,
            total_scripts=len(rows),
        )

        script_rows = [
            {
                "row_index": row.row_index,
                "external_id": row.external_id,
                "title": row.title,
                "script_text": row.script_text,
                "notes": row.notes,
                "detected_language_code": row.detected_language_code,
                "source_voice_preset": row.voice_hint,
                "status": "pending" if row.is_valid else "failed",
                "error_message": row.validation_error,
            }
            for row in rows
        ]
        await self._scripts.bulk_create(batch.id, script_rows)

        return batch

    async def start_batch(self, batch_id: uuid.UUID) -> BatchEntity:
        batch = await self._require_batch(batch_id)
        if batch.status not in ("draft", "failed"):
            raise BatchStateError(f"Batch is '{batch.status}' and cannot be (re)started.")

        await self._batches.update(batch_id, status="queued")
        self._orchestrator.start(batch_id)
        return await self._require_batch(batch_id)

    async def cancel_batch(self, batch_id: uuid.UUID) -> BatchEntity:
        batch = await self._require_batch(batch_id)
        if batch.status in ("completed", "failed", "cancelled"):
            raise BatchStateError(f"Batch is already '{batch.status}'.")

        await self._batches.update(batch_id, status="cancelled")
        self._orchestrator.cancel(batch_id)
        return await self._require_batch(batch_id)

    async def get_batch_detail(self, batch_id: uuid.UUID) -> BatchDetail:
        batch = await self._require_batch(batch_id)
        scripts = await self._scripts.list_by_batch(batch_id)
        jobs = await self._jobs.list_by_batch(batch_id)

        jobs_by_script: dict[uuid.UUID, list[JobEntity]] = {}
        for job in jobs:
            jobs_by_script.setdefault(job.script_id, []).append(job)

        script_outs = [
            ScriptOut(
                **{k: v for k, v in asdict(script).items() if k != "batch_id"},
                jobs=[JobOut(**asdict(job)) for job in jobs_by_script.get(script.id, [])],
            )
            for script in scripts
        ]

        return BatchDetail(**asdict(batch), scripts=script_outs)

    async def get_batch_status(self, batch_id: uuid.UUID) -> BatchStatusOut:
        batch = await self._require_batch(batch_id)
        scripts = await self._scripts.list_by_batch(batch_id)
        jobs = await self._jobs.list_by_batch(batch_id)

        jobs_by_script: dict[uuid.UUID, list[JobEntity]] = {}
        for job in jobs:
            jobs_by_script.setdefault(job.script_id, []).append(job)

        script_outs = [
            ScriptOut(
                **{k: v for k, v in asdict(script).items() if k != "batch_id"},
                jobs=[JobOut(**asdict(job)) for job in jobs_by_script.get(script.id, [])],
            )
            for script in scripts
        ]

        total = batch.total_jobs or len(jobs)
        percent = round((batch.completed_jobs + batch.failed_jobs) / total * 100, 1) if total else 0.0

        remaining = max(total - batch.completed_jobs - batch.failed_jobs, 0)
        audio_files = await self._audio_files.list_by_batch(batch_id)
        durations = [a.generation_time_ms for a in audio_files if a.generation_time_ms]
        eta_seconds = None
        if durations and remaining:
            avg_ms = sum(durations) / len(durations)
            eta_seconds = round((avg_ms / 1000) * remaining, 1)

        return BatchStatusOut(
            id=batch.id,
            status=batch.status,  # type: ignore[arg-type]
            total_scripts=batch.total_scripts,
            total_jobs=batch.total_jobs,
            completed_jobs=batch.completed_jobs,
            failed_jobs=batch.failed_jobs,
            percent_complete=percent,
            estimated_seconds_remaining=eta_seconds,
            scripts=script_outs,
        )

    async def get_download_url(self, batch_id: uuid.UUID) -> str:
        batch = await self._require_batch(batch_id)
        if not batch.zip_storage_path:
            raise BatchStateError("This batch's ZIP isn't ready yet.")
        return await self._storage.get_signed_url(self._batch_bucket, batch.zip_storage_path)

    async def estimate(self, script_count: int, language_count: int) -> BatchEstimateResponse:
        total_jobs = max(script_count, 0) * max(language_count, 1)
        average_ms = await self._audio_files.average_generation_time_ms()
        based_on_historical_data = average_ms is not None
        ms_per_job = average_ms if average_ms is not None else _FALLBACK_MS_PER_JOB

        # Jobs run concurrently up to the ElevenLabs concurrency ceiling, so
        # wall-clock time is roughly total work divided by how much of it
        # happens in parallel -- not a naive per-job sum.
        parallel_batches = max(1, -(-total_jobs // max(self._elevenlabs_max_concurrency, 1)))
        estimated_seconds = round((ms_per_job / 1000) * parallel_batches, 1)

        return BatchEstimateResponse(
            total_jobs=total_jobs,
            estimated_seconds=estimated_seconds,
            based_on_historical_data=based_on_historical_data,
        )

    async def _require_batch(self, batch_id: uuid.UUID) -> BatchEntity:
        batch = await self._batches.get(batch_id)
        if batch is None:
            raise BatchNotFoundError(f"Batch {batch_id} not found.")
        return batch
