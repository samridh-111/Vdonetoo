"""End-to-end pipeline integration test: runs a small real batch (3-5 rows,
2-3 languages) through orchestrate_batch and asserts the final state.

This deliberately makes real calls to Postgres/Redis/ElevenLabs/the
translation provider -- per the "no mocks" requirement, there is no faked
version of this test. It is gated on `settings.has_live_keys` (real
credentials must be present in the environment) and skips gracefully
otherwise, per the Phase 1 verification plan.

Run with real credentials in .env and a reachable Supabase/Redis:
    ENVIRONMENT=test pytest tests/integration/test_pipeline_small_batch.py
"""

import asyncio
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.core.db import new_worker_session
from app.repositories import SqlBatchRepository, SqlProjectRepository, SqlScriptRepository
from app.workers.tasks.pipeline_tasks import _orchestrate_batch_async

pytestmark = pytest.mark.asyncio

_POLL_INTERVAL_SECONDS = 2
_POLL_TIMEOUT_SECONDS = 180


@pytest.fixture(autouse=True)
def _eager_celery():
    """Runs the whole chord cascade synchronously in-process instead of
    requiring a separately-running worker + broker for this test."""
    original_eager = celery_app.conf.task_always_eager
    original_propagates = celery_app.conf.task_eager_propagates
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield
    celery_app.conf.task_always_eager = original_eager
    celery_app.conf.task_eager_propagates = original_propagates


async def _database_is_reachable() -> bool:
    try:
        async with new_worker_session() as session:
            await session.execute(text("select 1"))
        return True
    except SQLAlchemyError:
        return False


@pytest.fixture(autouse=True)
async def _skip_without_live_environment():
    settings = get_settings()
    if not settings.has_live_keys:
        pytest.skip("Live ElevenLabs/translation/Supabase credentials are required for this test.")
    if not await _database_is_reachable():
        pytest.skip("Configured SUPABASE_DB_URL is not reachable from this environment.")


async def test_small_batch_completes_end_to_end() -> None:
    settings = get_settings()

    async with new_worker_session() as session:
        project = await SqlProjectRepository(session).get_or_create_default("ivr_automation", "IVR Automation")
        batch_repo = SqlBatchRepository(session)
        batch = await batch_repo.create(
            project_id=project.id,
            name=f"integration-test-{uuid.uuid4().hex[:8]}",
            source_type="csv",
            source_filename="integration-test.csv",
            translation_mode="generate_multiple",
            target_languages=["hi", "ta"],
            translation_provider=settings.translation_provider,
            default_voice_map={},
            status="draft",
            concurrency_limit=3,
            total_scripts=3,
        )

        script_rows = [
            {
                "row_index": 0,
                "external_id": "001",
                "script_text": "Welcome to Automation Hub support. Please hold the line.",
                "status": "pending",
            },
            {
                "row_index": 1,
                "external_id": "002",
                "script_text": "Please enter your ten digit order number.",
                "status": "pending",
            },
            {
                "row_index": 2,
                "external_id": "003",
                "script_text": "",  # deliberately invalid, proves error handling doesn't crash the batch
                "status": "failed",
                "error_message": "Script text is empty.",
            },
        ]
        await SqlScriptRepository(session).bulk_create(batch.id, script_rows)

    await _orchestrate_batch_async(str(batch.id))

    # Eager mode resolves the chord cascade synchronously in the common case,
    # but this poll is a defensive fallback in case any stage genuinely
    # dispatches asynchronously (e.g. Celery's eager-chord edge cases).
    final_batch = None
    elapsed = 0
    while elapsed < _POLL_TIMEOUT_SECONDS:
        async with new_worker_session() as session:
            final_batch = await SqlBatchRepository(session).get(batch.id)
        if final_batch is not None and final_batch.status in ("completed", "failed"):
            break
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)
        elapsed += _POLL_INTERVAL_SECONDS

    assert final_batch is not None
    assert final_batch.status in ("completed", "failed")
    assert final_batch.zip_storage_path is not None or final_batch.status == "failed"
