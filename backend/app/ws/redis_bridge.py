import asyncio
import uuid
from functools import lru_cache

from app.core.logging import get_logger
from app.core.redis_client import get_redis
from app.ws.connection_manager import ConnectionManager

logger = get_logger(__name__)


class RedisBridge:
    """Lazily subscribes to a batch's Redis progress channel only while at
    least one WebSocket client is connected for that batch (refcounted), and
    forwards every message verbatim to the ConnectionManager."""

    def __init__(self, connection_manager: ConnectionManager) -> None:
        self._manager = connection_manager
        self._tasks: dict[uuid.UUID, asyncio.Task[None]] = {}
        self._refcounts: dict[uuid.UUID, int] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, batch_id: uuid.UUID) -> None:
        async with self._lock:
            self._refcounts[batch_id] = self._refcounts.get(batch_id, 0) + 1
            if batch_id not in self._tasks:
                self._tasks[batch_id] = asyncio.create_task(self._listen(batch_id))

    async def unsubscribe(self, batch_id: uuid.UUID) -> None:
        async with self._lock:
            if batch_id not in self._refcounts:
                return
            self._refcounts[batch_id] -= 1
            if self._refcounts[batch_id] <= 0:
                del self._refcounts[batch_id]
                task = self._tasks.pop(batch_id, None)
                if task is not None:
                    task.cancel()

    async def _listen(self, batch_id: uuid.UUID) -> None:
        redis = get_redis()
        pubsub = redis.pubsub()
        channel = f"batch:{batch_id}:progress"
        await pubsub.subscribe(channel)
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                await self._manager.broadcast(batch_id, message["data"])
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("redis_bridge_listen_failed", batch_id=str(batch_id))
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()


@lru_cache
def get_redis_bridge(connection_manager: ConnectionManager) -> RedisBridge:
    return RedisBridge(connection_manager)
