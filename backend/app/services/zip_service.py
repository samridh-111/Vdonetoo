import csv
import io
import json
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from app.domain.entities import VoiceEntity
from app.domain.interfaces.repositories import (
    AudioFileRepository,
    BatchRepository,
    JobRepository,
    LogRepository,
    ScriptRepository,
    TranslationRepository,
    VoiceRepository,
)
from app.domain.interfaces.storage_provider import StorageProvider

_METADATA_FIELDS = [
    "Script ID",
    "Original Text",
    "Translated Text",
    "Language",
    "Voice",
    "Duration",
    "Generation Time",
    "Status",
    "File Path",
]


class ZipService:
    """Assembles the final downloadable ZIP for a batch: per-language folders
    of numbered mp3s, metadata.csv, logs.txt, and summary.json -- then
    uploads it to Supabase Storage and returns the storage path."""

    def __init__(
        self,
        batch_repository: BatchRepository,
        script_repository: ScriptRepository,
        job_repository: JobRepository,
        audio_file_repository: AudioFileRepository,
        translation_repository: TranslationRepository,
        log_repository: LogRepository,
        voice_repository: VoiceRepository,
        storage_provider: StorageProvider,
        audio_bucket: str,
        batch_bucket: str,
    ) -> None:
        self._batches = batch_repository
        self._scripts = script_repository
        self._jobs = job_repository
        self._audio_files = audio_file_repository
        self._translations = translation_repository
        self._logs = log_repository
        self._voices = voice_repository
        self._storage = storage_provider
        self._audio_bucket = audio_bucket
        self._batch_bucket = batch_bucket

    async def build_and_upload(self, batch_id: uuid.UUID) -> str:
        batch = await self._batches.get(batch_id)
        scripts_by_id = {s.id: s for s in await self._scripts.list_by_batch(batch_id)}
        jobs = await self._jobs.list_by_batch(batch_id)
        audio_by_job_id = {a.job_id: a for a in await self._audio_files.list_by_batch(batch_id)}
        logs = await self._logs.list_by_batch(batch_id)

        translation_ids = [job.translation_id for job in jobs if job.translation_id is not None]
        translations_by_id = {t.id: t for t in await self._translations.list_by_ids(translation_ids)}

        voice_cache: dict[uuid.UUID, VoiceEntity | None] = {}

        async def resolve_voice(voice_id: uuid.UUID | None) -> VoiceEntity | None:
            if voice_id is None:
                return None
            if voice_id not in voice_cache:
                voice_cache[voice_id] = await self._voices.get(voice_id)
            return voice_cache[voice_id]

        with TemporaryDirectory() as tmpdir:
            content_root = Path(tmpdir) / "content"
            content_root.mkdir()

            metadata_rows: list[dict[str, str]] = []
            for job in jobs:
                script = scripts_by_id.get(job.script_id)
                audio = audio_by_job_id.get(job.id)
                voice = await resolve_voice(job.voice_id)

                file_path_in_zip = ""
                if audio is not None:
                    lang_dir = content_root / job.language_code
                    lang_dir.mkdir(exist_ok=True)
                    stem = script.external_id if script and script.external_id else str(job.script_id)[:8]
                    row_index = script.row_index if script else 0
                    filename = f"{row_index:04d}_{stem}.mp3"
                    file_path_in_zip = f"{job.language_code}/{filename}"
                    audio_bytes = await self._storage.download(self._audio_bucket, audio.storage_path)
                    (lang_dir / filename).write_bytes(audio_bytes)

                translation = translations_by_id.get(job.translation_id) if job.translation_id else None

                metadata_rows.append(
                    {
                        "Script ID": (script.external_id or str(script.id)) if script else "",
                        "Original Text": script.script_text if script else "",
                        "Translated Text": (translation.translated_text or "") if translation else "",
                        "Language": job.language_code,
                        "Voice": voice.name if voice else "",
                        "Duration": f"{audio.duration_seconds:.2f}" if audio and audio.duration_seconds else "",
                        "Generation Time": str(audio.generation_time_ms) if audio and audio.generation_time_ms else "",
                        "Status": job.stage,
                        "File Path": file_path_in_zip,
                    }
                )

            metadata_buffer = io.StringIO()
            writer = csv.DictWriter(metadata_buffer, fieldnames=_METADATA_FIELDS)
            writer.writeheader()
            writer.writerows(metadata_rows)
            (content_root / "metadata.csv").write_text(metadata_buffer.getvalue())

            logs_lines = [
                f"[{log.created_at.isoformat()}] {log.level.upper():7s} {log.message}" for log in logs
            ]
            (content_root / "logs.txt").write_text("\n".join(logs_lines) + ("\n" if logs_lines else ""))

            completed_count, failed_count = await self._batches.recompute_job_counts(batch_id)
            duration_seconds = None
            if batch and batch.started_at:
                end = batch.completed_at or datetime.now(UTC)
                duration_seconds = (end - batch.started_at).total_seconds()

            summary = {
                "batch_id": str(batch_id),
                "name": batch.name if batch else "",
                "total_scripts": batch.total_scripts if batch else len(scripts_by_id),
                "total_jobs": len(jobs),
                "completed_jobs": completed_count,
                "failed_jobs": failed_count,
                "languages": sorted({job.language_code for job in jobs}),
                "started_at": batch.started_at.isoformat() if batch and batch.started_at else None,
                "completed_at": (batch.completed_at or datetime.now(UTC)).isoformat() if batch else None,
                "duration_seconds": duration_seconds,
            }
            (content_root / "summary.json").write_text(json.dumps(summary, indent=2))

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_path in sorted(content_root.rglob("*")):
                    if file_path.is_file():
                        zf.write(file_path, arcname=str(file_path.relative_to(content_root)))

        date_str = datetime.now(UTC).strftime("%Y_%m_%d")
        zip_filename = f"Batch_{date_str}_{str(batch_id)[:8]}.zip"
        storage_path = f"batches/{batch_id}/{zip_filename}"

        await self._storage.upload(self._batch_bucket, storage_path, zip_buffer.getvalue(), "application/zip")
        return storage_path
