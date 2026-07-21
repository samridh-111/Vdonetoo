import asyncio
import uuid
from typing import Any

from app.core.celery_app import celery_app
from app.core.db import new_worker_session
from app.repositories import (
    SqlBatchRepository,
    SqlJobRepository,
    SqlLanguageRepository,
    SqlLogRepository,
    SqlScriptRepository,
    SqlTranslationRepository,
)
from app.workers.cancellation import is_batch_cancelled
from app.workers.factories import (
    build_translation_service,
    build_voice_resolution_service,
    get_translation_provider,
)
from app.workers.progress import publish_progress

MAX_PREPARE_ATTEMPTS = 3


def _resolve_target_languages(
    translation_mode: str,
    detected_code: str,
    batch_target_languages: list[str],
    all_active_codes: list[str],
) -> list[str]:
    if translation_mode == "keep_original":
        return [detected_code]
    if translation_mode == "translate_everything":
        return sorted(set(all_active_codes))
    # "translate_selected" and "generate_multiple" both mean "generate audio
    # in exactly these configured languages" -- the former frames it as
    # picking from existing languages, the latter as fanning out to several,
    # but both drive off the same batch.target_languages list. Include the
    # detected/source language in target_languages too if the original
    # should be kept alongside the translations.
    selected = sorted(set(batch_target_languages))
    return selected or [detected_code]


@celery_app.task(
    name="app.workers.tasks.script_tasks.prepare_script",
    bind=True,
    max_retries=MAX_PREPARE_ATTEMPTS,
)
def prepare_script(self: Any, script_id: str) -> dict[str, Any]:
    try:
        return asyncio.run(_prepare_script_async(script_id))
    except Exception as exc:  # noqa: BLE001 -- deliberately broad: any failure here must not crash the chord
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=5 * (self.request.retries + 1)) from exc
        asyncio.run(_mark_script_failed_async(script_id, str(exc)))
        return {"script_id": script_id, "status": "failed", "error": str(exc)}


async def _mark_script_failed_async(script_id: str, error_message: str) -> None:
    script_uuid = uuid.UUID(script_id)
    async with new_worker_session() as session:
        script_repo = SqlScriptRepository(session)
        script = await script_repo.get(script_uuid)
        await script_repo.update(script_uuid, status="failed", error_message=error_message)
        if script is not None:
            await SqlLogRepository(session).create(
                script.batch_id,
                f"Script #{script.row_index} failed after {MAX_PREPARE_ATTEMPTS} attempts: {error_message}",
                level="error",
                script_id=script_uuid,
            )
            publish_progress(
                script.batch_id,
                "script_stage_changed",
                {"script_id": script_id, "status": "failed", "error": error_message},
            )


async def _prepare_script_async(script_id: str) -> dict[str, Any]:
    script_uuid = uuid.UUID(script_id)

    async with new_worker_session() as session:
        script_repo = SqlScriptRepository(session)
        batch_repo = SqlBatchRepository(session)
        job_repo = SqlJobRepository(session)
        translation_repo = SqlTranslationRepository(session)
        log_repo = SqlLogRepository(session)
        language_repo = SqlLanguageRepository(session)

        script = await script_repo.get(script_uuid)
        if script is None or script.status == "failed":
            return {"script_id": script_id, "status": "skipped"}

        batch = await batch_repo.get(script.batch_id)
        if batch is None:
            return {"script_id": script_id, "status": "skipped"}

        if is_batch_cancelled(batch.id):
            return {"script_id": script_id, "status": "cancelled"}

        await script_repo.update(script_uuid, status="translating")
        publish_progress(batch.id, "script_stage_changed", {"script_id": script_id, "status": "translating"})

        detected_code = script.detected_language_code or "en"
        active_languages = await language_repo.list_active()
        target_codes = _resolve_target_languages(
            batch.translation_mode, detected_code, batch.target_languages, [lang.code for lang in active_languages]
        )

        translation_service = build_translation_service(session)
        voice_service = build_voice_resolution_service(session)
        provider = get_translation_provider(batch.translation_provider)

        job_rows: list[dict[str, Any]] = []
        for target_code in target_codes:
            if target_code == detected_code:
                translation = await translation_repo.create(
                    script_id=script_uuid,
                    source_language_code=detected_code,
                    target_language_code=target_code,
                    provider="none",
                    translated_text=script.script_text,
                    status="completed",
                )
            else:
                try:
                    translated_text = await translation_service.translate(
                        provider, script.script_text, detected_code, target_code
                    )
                    translation = await translation_repo.create(
                        script_id=script_uuid,
                        source_language_code=detected_code,
                        target_language_code=target_code,
                        provider=batch.translation_provider,
                        translated_text=translated_text,
                        status="completed",
                    )
                except Exception as exc:  # noqa: BLE001 -- one language's translation failure must not sink the others
                    await translation_repo.create(
                        script_id=script_uuid,
                        source_language_code=detected_code,
                        target_language_code=target_code,
                        provider=batch.translation_provider,
                        translated_text=None,
                        status="failed",
                        error_message=str(exc),
                    )
                    await log_repo.create(
                        batch.id,
                        f"Translation to {target_code} failed for script #{script.row_index}: {exc}",
                        level="error",
                        script_id=script_uuid,
                    )
                    continue

            voice = await voice_service.resolve(
                voice_hint=script.source_voice_preset,
                default_voice_map=batch.default_voice_map,
                language_code=target_code,
            )
            job_rows.append(
                {
                    "batch_id": batch.id,
                    "script_id": script_uuid,
                    "translation_id": translation.id,
                    "language_code": target_code,
                    "voice_id": voice.id if voice else None,
                    "stage": "queued",
                }
            )

        if not job_rows:
            await script_repo.update(
                script_uuid, status="failed", error_message="No target languages could be prepared."
            )
            await log_repo.create(
                batch.id,
                f"Script #{script.row_index} failed: no target languages could be prepared.",
                level="error",
                script_id=script_uuid,
            )
            publish_progress(batch.id, "script_stage_changed", {"script_id": script_id, "status": "failed"})
            return {"script_id": script_id, "status": "failed"}

        await job_repo.bulk_create(job_rows)
        await script_repo.update(script_uuid, status="generating")
        publish_progress(batch.id, "script_stage_changed", {"script_id": script_id, "status": "generating"})
        return {"script_id": script_id, "status": "prepared", "job_count": len(job_rows)}
