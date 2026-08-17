import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import AudioFileEntity
from app.models import AudioFile


def _to_entity(row: AudioFile) -> AudioFileEntity:
    return AudioFileEntity(
        id=row.id,
        job_id=row.job_id,
        script_id=row.script_id,
        batch_id=row.batch_id,
        language_code=row.language_code,
        voice_id=row.voice_id,
        storage_path=row.storage_path,
        public_url=row.public_url,
        duration_seconds=float(row.duration_seconds) if row.duration_seconds is not None else None,
        file_size_bytes=row.file_size_bytes,
        generation_time_ms=row.generation_time_ms,
        created_at=row.created_at,
    )


class SqlAudioFileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **fields: Any) -> AudioFileEntity:
        row = AudioFile(**fields)
        self._session.add(row)
        await self._session.flush()
        await self._session.commit()
        return _to_entity(row)

    async def list_by_batch(self, batch_id: uuid.UUID) -> list[AudioFileEntity]:
        result = await self._session.execute(select(AudioFile).where(AudioFile.batch_id == batch_id))
        return [_to_entity(row) for row in result.scalars().all()]

    async def average_generation_time_ms(self, sample_size: int = 50) -> float | None:
        recent_ids_subquery = (
            select(AudioFile.id)
            .where(AudioFile.generation_time_ms.is_not(None))
            .order_by(AudioFile.created_at.desc())
            .limit(sample_size)
            .subquery()
        )
        result = await self._session.execute(
            select(func.avg(AudioFile.generation_time_ms)).where(AudioFile.id.in_(select(recent_ids_subquery.c.id)))
        )
        average = result.scalar_one_or_none()
        return float(average) if average is not None else None
