import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class TranslationEntity:
    id: uuid.UUID
    script_id: uuid.UUID
    source_language_code: str | None
    target_language_code: str
    provider: str
    translated_text: str | None
    status: str
    error_message: str | None
    created_at: datetime
