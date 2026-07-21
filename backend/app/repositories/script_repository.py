import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import ScriptEntity
from app.models import Script


def _to_entity(row: Script) -> ScriptEntity:
    return ScriptEntity(
        id=row.id,
        batch_id=row.batch_id,
        row_index=row.row_index,
        external_id=row.external_id,
        title=row.title,
        script_text=row.script_text,
        notes=row.notes,
        detected_language_code=row.detected_language_code,
        source_voice_preset=row.source_voice_preset,
        status=row.status,
        error_message=row.error_message,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlScriptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_create(self, batch_id: uuid.UUID, rows: list[dict[str, Any]]) -> list[ScriptEntity]:
        entities = [Script(batch_id=batch_id, **row) for row in rows]
        self._session.add_all(entities)
        await self._session.flush()
        await self._session.commit()
        return [_to_entity(row) for row in entities]

    async def list_by_batch(self, batch_id: uuid.UUID) -> list[ScriptEntity]:
        result = await self._session.execute(
            select(Script).where(Script.batch_id == batch_id).order_by(Script.row_index)
        )
        return [_to_entity(row) for row in result.scalars().all()]

    async def get(self, script_id: uuid.UUID) -> ScriptEntity | None:
        row = await self._session.get(Script, script_id)
        return _to_entity(row) if row else None

    async def update(self, script_id: uuid.UUID, **fields: Any) -> None:
        await self._session.execute(update(Script).where(Script.id == script_id).values(**fields))
        await self._session.commit()
