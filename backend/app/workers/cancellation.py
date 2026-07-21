import uuid

from app.core.redis_client import get_sync_redis


def is_batch_cancelled(batch_id: uuid.UUID) -> bool:
    """Every task checks this flag at its top. This is the pragmatic Phase 1
    cancel semantic: true mid-flight Celery task revocation against an
    in-progress ElevenLabs call isn't reliable, so cancellation instead
    short-circuits any *remaining* queued work."""
    return get_sync_redis().get(f"batch:{batch_id}:cancelled") is not None
