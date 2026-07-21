import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ScriptEntity:
    id: uuid.UUID
    batch_id: uuid.UUID
    row_index: int
    external_id: str | None
    title: str | None
    script_text: str
    notes: str | None
    detected_language_code: str | None
    source_voice_preset: str | None
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime
