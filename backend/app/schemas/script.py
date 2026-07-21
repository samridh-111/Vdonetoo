import uuid
from datetime import datetime

from pydantic import BaseModel


class JobOut(BaseModel):
    id: uuid.UUID
    language_code: str
    voice_id: uuid.UUID | None
    stage: str
    attempt: int
    max_attempts: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class ScriptOut(BaseModel):
    id: uuid.UUID
    row_index: int
    external_id: str | None
    title: str | None
    script_text: str
    notes: str | None
    detected_language_code: str | None
    status: str
    error_message: str | None
    jobs: list[JobOut] = []

    model_config = {"from_attributes": True}
