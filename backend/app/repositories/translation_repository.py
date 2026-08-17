import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import TranslationEntity
from app.models import Translation


def _to_entity(row: Translation) -> TranslationEntity:
    return TranslationEntity(
        id=row.id,
        script_id=row.script_id,
        source_language_code=row.source_language_code,
        target_language_code=row.target_language_code,
        provider=row.provider,
        translated_text=row.translated_text,
        status=row.status,
        error_message=row.error_message,
        created_at=row.created_at,
    )


class SqlTranslationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **fields: Any) -> TranslationEntity:
        row = Translation(**fields)
        self._session.add(row)
        await self._session.flush()
        await self._session.commit()
        return _to_entity(row)

    async def get(self, translation_id: uuid.UUID) -> TranslationEntity | None:
        row = await self._session.get(Translation, translation_id)
        return _to_entity(row) if row else None

    async def list_by_ids(self, translation_ids: list[uuid.UUID]) -> list[TranslationEntity]:
        if not translation_ids:
            return []
        result = await self._session.execute(select(Translation).where(Translation.id.in_(translation_ids)))
        return [_to_entity(row) for row in result.scalars().all()]

    async def update(self, translation_id: uuid.UUID, **fields: Any) -> None:
        await self._session.execute(
            update(Translation).where(Translation.id == translation_id).values(**fields)
        )
        await self._session.commit()
