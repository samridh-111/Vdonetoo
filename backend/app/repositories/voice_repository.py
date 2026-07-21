import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import VoiceEntity
from app.models import Voice


def _to_entity(row: Voice) -> VoiceEntity:
    return VoiceEntity(
        id=row.id,
        name=row.name,
        preset_key=row.preset_key,
        elevenlabs_voice_id=row.elevenlabs_voice_id,
        language_code=row.language_code,
        similarity=float(row.similarity),
        stability=float(row.stability),
        style=float(row.style),
        speed=float(row.speed),
        sample_audio_url=row.sample_audio_url,
        is_active=row.is_active,
        created_at=row.created_at,
    )


class SqlVoiceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self, language_code: str | None = None) -> list[VoiceEntity]:
        query = select(Voice).where(Voice.is_active.is_(True))
        if language_code is not None:
            query = query.where(Voice.language_code == language_code)
        result = await self._session.execute(query.order_by(Voice.name))
        return [_to_entity(row) for row in result.scalars().all()]

    async def get(self, voice_id: uuid.UUID) -> VoiceEntity | None:
        row = await self._session.get(Voice, voice_id)
        return _to_entity(row) if row else None

    async def get_by_preset_key(self, preset_key: str) -> VoiceEntity | None:
        result = await self._session.execute(select(Voice).where(Voice.preset_key == preset_key))
        row = result.scalar_one_or_none()
        return _to_entity(row) if row else None

    async def first_active_for_language(self, language_code: str) -> VoiceEntity | None:
        result = await self._session.execute(
            select(Voice)
            .where(Voice.is_active.is_(True), Voice.language_code == language_code)
            .order_by(Voice.name)
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return _to_entity(row) if row else None

    async def get_fallback(self) -> VoiceEntity | None:
        return await self.get_by_preset_key("professional")
