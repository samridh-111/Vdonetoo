import uuid
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import JobEntity
from app.models import Job


def _to_entity(row: Job) -> JobEntity:
    return JobEntity(
        id=row.id,
        batch_id=row.batch_id,
        script_id=row.script_id,
        translation_id=row.translation_id,
        language_code=row.language_code,
        voice_id=row.voice_id,
        celery_task_id=row.celery_task_id,
        stage=row.stage,
        attempt=row.attempt,
        max_attempts=row.max_attempts,
        error_message=row.error_message,
        started_at=row.started_at,
        completed_at=row.completed_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_create(self, rows: list[dict[str, Any]]) -> list[JobEntity]:
        entities = [Job(**row) for row in rows]
        self._session.add_all(entities)
        await self._session.flush()
        await self._session.commit()
        return [_to_entity(row) for row in entities]

    async def list_by_batch(self, batch_id: uuid.UUID) -> list[JobEntity]:
        result = await self._session.execute(select(Job).where(Job.batch_id == batch_id))
        return [_to_entity(row) for row in result.scalars().all()]

    async def list_by_stage(self, batch_id: uuid.UUID, stage: str) -> list[JobEntity]:
        result = await self._session.execute(
            select(Job).where(Job.batch_id == batch_id, Job.stage == stage)
        )
        return [_to_entity(row) for row in result.scalars().all()]

    async def get(self, job_id: uuid.UUID) -> JobEntity | None:
        row = await self._session.get(Job, job_id)
        return _to_entity(row) if row else None

    async def update(self, job_id: uuid.UUID, **fields: Any) -> None:
        fields["updated_at"] = func.now()
        await self._session.execute(update(Job).where(Job.id == job_id).values(**fields))
        await self._session.commit()

    async def count_by_stage(self, batch_id: uuid.UUID) -> dict[str, int]:
        result = await self._session.execute(
            select(Job.stage, func.count()).where(Job.batch_id == batch_id).group_by(Job.stage)
        )
        return {stage: int(count) for stage, count in result.all()}
