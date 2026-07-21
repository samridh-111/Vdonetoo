import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class VoiceEntity:
    id: uuid.UUID
    name: str
    preset_key: str
    elevenlabs_voice_id: str
    language_code: str | None
    similarity: float
    stability: float
    style: float
    speed: float
    sample_audio_url: str | None
    is_active: bool
    created_at: datetime
