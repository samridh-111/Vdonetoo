import uuid
from typing import Any

from app.core.redis_client import get_sync_redis
from app.schemas.websocket import WSProgressMessage


def publish_progress(batch_id: uuid.UUID, message_type: str, data: dict[str, Any]) -> None:
    """Writes are always to Postgres first (the source of truth); this is the
    fire-and-forget notification fan-out to whatever WebSocket clients are
    currently subscribed to `batch:{batch_id}:progress` via app/ws/redis_bridge.py."""
    message = WSProgressMessage(type=message_type, batch_id=batch_id, data=data)  # type: ignore[arg-type]
    get_sync_redis().publish(f"batch:{batch_id}:progress", message.model_dump_json())
