import uuid

from redis import Redis

_CANCEL_FLAG_TTL_SECONDS = 24 * 60 * 60


class PipelineOrchestrator:
    """Thin boundary between the FastAPI request layer and Celery. Kept as
    its own service (rather than calling `.delay()` directly from the API
    router) so batch_service.py doesn't need to import Celery task modules,
    keeping the web layer decoupled from worker internals."""

    def __init__(self, sync_redis: Redis) -> None:
        self._redis = sync_redis

    def start(self, batch_id: uuid.UUID) -> None:
        from app.workers.tasks.pipeline_tasks import orchestrate_batch

        orchestrate_batch.delay(str(batch_id))

    def cancel(self, batch_id: uuid.UUID) -> None:
        self._redis.set(f"batch:{batch_id}:cancelled", "1", ex=_CANCEL_FLAG_TTL_SECONDS)

    def is_cancelled(self, batch_id: uuid.UUID) -> bool:
        return self._redis.get(f"batch:{batch_id}:cancelled") is not None
