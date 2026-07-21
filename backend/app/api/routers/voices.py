import base64
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import SettingsDep, get_elevenlabs_provider, get_voice_repository, get_voice_resolution_service
from app.domain.interfaces.voice_provider import VoiceProvider
from app.repositories import SqlVoiceRepository
from app.schemas.voice import VoiceOut, VoicePreviewResponse
from app.services.voice_service import VoiceResolutionService

router = APIRouter(prefix="/voices", tags=["voices"])


@router.get("", response_model=list[VoiceOut])
async def list_voices(
    voice_repository: Annotated[SqlVoiceRepository, Depends(get_voice_repository)],
    language: str | None = None,
) -> list[VoiceOut]:
    voices = await voice_repository.list_active(language_code=language)
    return [VoiceOut.model_validate(voice) for voice in voices]


@router.post("/{voice_id}/preview", response_model=VoicePreviewResponse)
async def preview_voice(
    voice_id: uuid.UUID,
    voice_repository: Annotated[SqlVoiceRepository, Depends(get_voice_repository)],
    voice_service: Annotated[VoiceResolutionService, Depends(get_voice_resolution_service)],
    voice_provider: Annotated[VoiceProvider, Depends(get_elevenlabs_provider)],
    settings: SettingsDep,
) -> VoicePreviewResponse:
    voice = await voice_repository.get(voice_id)
    if voice is None:
        raise HTTPException(404, f"Voice {voice_id} not found.")

    audio_bytes = await voice_service.generate_preview(voice, voice_provider, settings.elevenlabs_preview_text)
    return VoicePreviewResponse(voice_id=voice_id, audio_base64=base64.b64encode(audio_bytes).decode("ascii"))
