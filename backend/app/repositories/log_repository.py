import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import LogEntity
from app.models import Log


def _to_entity(row: Log) -> LogEntity:
    return LogEntity(
        id=row.id,
        batch_id=row.batch_id,
        script_id=row.script_id,
        job_id=row.job_id,
        level=row.level,
        message=row.message,
        context=row.context,
        created_at=row.created_at,
    )


class SqlLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        batch_id: uuid.UUID,
        message: str,
        *,
        level: str = "info",
        script_id: uuid.UUID | None = None,
        job_id: uuid.UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> LogEntity:
        row = Log(
            batch_id=batch_id,
            message=message,
            level=level,
            script_id=script_id,
            job_id=job_id,
            context=context,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.commit()
        return _to_entity(row)

    async def list_by_batch(self, batch_id: uuid.UUID) -> list[LogEntity]:
        result = await self._session.execute(
            select(Log).where(Log.batch_id == batch_id).order_by(Log.created_at)
        )
        return [_to_entity(row) for row in result.scalars().all()]
