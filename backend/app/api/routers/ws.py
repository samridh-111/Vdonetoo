import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws.connection_manager import get_connection_manager
from app.ws.redis_bridge import get_redis_bridge

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/batch/{batch_id}")
async def batch_progress_ws(websocket: WebSocket, batch_id: uuid.UUID) -> None:
    manager = get_connection_manager()
    bridge = get_redis_bridge(manager)

    await websocket.accept()
    manager.add(batch_id, websocket)
    await bridge.subscribe(batch_id)

    try:
        while True:
            # No client->server protocol is expected; this just blocks until
            # the client disconnects (or sends anything, which we ignore).
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.remove(batch_id, websocket)
        await bridge.unsubscribe(batch_id)
