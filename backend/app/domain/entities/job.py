import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class JobEntity:
    id: uuid.UUID
    batch_id: uuid.UUID
    script_id: uuid.UUID
    translation_id: uuid.UUID | None
    language_code: str
    voice_id: uuid.UUID | None
    celery_task_id: str | None
    stage: str
    attempt: int
    max_attempts: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
