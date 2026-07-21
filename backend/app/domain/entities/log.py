import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class LogEntity:
    id: uuid.UUID
    batch_id: uuid.UUID
    script_id: uuid.UUID | None
    job_id: uuid.UUID | None
    level: str
    message: str
    context: dict[str, Any] | None
    created_at: datetime
