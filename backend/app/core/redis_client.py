from functools import lru_cache

from redis import asyncio as aioredis
from redis import Redis as SyncRedis

from app.core.config import get_settings


@lru_cache
def get_redis() -> aioredis.Redis:
    """Async Redis client, used by FastAPI/WebSocket code and async services."""
    settings = get_settings()
    return aioredis.from_url(settings.redis_url, decode_responses=True)  # type: ignore[no-any-return,no-untyped-call]


@lru_cache
def get_sync_redis() -> SyncRedis:
    """Sync Redis client, used inside Celery tasks which run in a sync context."""
    settings = get_settings()
    return SyncRedis.from_url(settings.redis_url, decode_responses=True)
