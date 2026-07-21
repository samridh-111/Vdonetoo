import uuid
from functools import lru_cache

from fastapi import WebSocket


class ConnectionManager:
    """Tracks which WebSocket clients are subscribed to which batch's
    progress stream, so app/ws/redis_bridge.py knows who to fan messages out
    to and when a batch has zero remaining subscribers."""

    def __init__(self) -> None:
        self._connections: dict[uuid.UUID, set[WebSocket]] = {}

    def add(self, batch_id: uuid.UUID, websocket: WebSocket) -> None:
        self._connections.setdefault(batch_id, set()).add(websocket)

    def remove(self, batch_id: uuid.UUID, websocket: WebSocket) -> None:
        connections = self._connections.get(batch_id)
        if connections is None:
            return
        connections.discard(websocket)
        if not connections:
            del self._connections[batch_id]

    def connection_count(self, batch_id: uuid.UUID) -> int:
        return len(self._connections.get(batch_id, ()))

    async def broadcast(self, batch_id: uuid.UUID, message: str) -> None:
        for websocket in list(self._connections.get(batch_id, ())):
            try:
                await websocket.send_text(message)
            except Exception:  # noqa: BLE001 -- a dead socket must not stop the broadcast to everyone else
                self.remove(batch_id, websocket)


@lru_cache
def get_connection_manager() -> ConnectionManager:
    return ConnectionManager()
