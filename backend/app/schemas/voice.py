import uuid

from pydantic import BaseModel


class VoiceOut(BaseModel):
    id: uuid.UUID
    name: str
    preset_key: str
    language_code: str | None
    similarity: float
    stability: float
    style: float
    speed: float
    sample_audio_url: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class VoicePreviewResponse(BaseModel):
    voice_id: uuid.UUID
    audio_base64: str
    content_type: str = "audio/mpeg"
