import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class UserEntity:
    id: uuid.UUID
    email: str
    display_name: str | None
    role: str
    created_at: datetime
