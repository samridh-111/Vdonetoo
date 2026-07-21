import uuid
from typing import Any, Literal

from pydantic import BaseModel


class WSProgressMessage(BaseModel):
    """Payload published to Redis channel `batch:{batch_id}:progress` and
    forwarded verbatim to every connected WebSocket client for that batch."""

    type: Literal[
        "script_stage_changed",
        "job_stage_changed",
        "batch_progress",
        "batch_completed",
        "batch_failed",
        "batch_cancelled",
    ]
    batch_id: uuid.UUID
    data: dict[str, Any]
