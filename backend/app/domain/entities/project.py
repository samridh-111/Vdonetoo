import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ProjectEntity:
    id: uuid.UUID
    name: str
    description: str | None
    module: str
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
