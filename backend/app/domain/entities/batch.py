import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class BatchEntity:
    id: uuid.UUID
    project_id: uuid.UUID | None
    name: str
    source_type: str
    source_filename: str | None
    source_url: str | None
    translation_mode: str
    target_languages: list[str]
    translation_provider: str
    default_voice_map: dict[str, str]
    status: str
    concurrency_limit: int
    total_scripts: int
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    zip_storage_path: str | None
    created_by: uuid.UUID | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    updated_at: datetime
