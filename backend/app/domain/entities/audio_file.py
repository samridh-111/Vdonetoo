import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AudioFileEntity:
    id: uuid.UUID
    job_id: uuid.UUID
    script_id: uuid.UUID
    batch_id: uuid.UUID
    language_code: str
    voice_id: uuid.UUID | None
    storage_path: str
    public_url: str | None
    duration_seconds: float | None
    file_size_bytes: int | None
    generation_time_ms: int | None
    created_at: datetime
