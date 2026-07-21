import uuid
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import BatchEntity
from app.models import Batch, Job


def _to_entity(row: Batch) -> BatchEntity:
    return BatchEntity(
        id=row.id,
        project_id=row.project_id,
        name=row.name,
        source_type=row.source_type,
        source_filename=row.source_filename,
        source_url=row.source_url,
        translation_mode=row.translation_mode,
        target_languages=list(row.target_languages or []),
        translation_provider=row.translation_provider,
        default_voice_map=dict(row.default_voice_map or {}),
        status=row.status,
        concurrency_limit=row.concurrency_limit,
        total_scripts=row.total_scripts,
        total_jobs=row.total_jobs,
        completed_jobs=row.completed_jobs,
        failed_jobs=row.failed_jobs,
        zip_storage_path=row.zip_storage_path,
        created_by=row.created_by,
        created_at=row.created_at,
        started_at=row.started_at,
        completed_at=row.completed_at,
        updated_at=row.updated_at,
    )


class SqlBatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **fields: Any) -> BatchEntity:
        row = Batch(**fields)
        self._session.add(row)
        await self._session.flush()
        await self._session.commit()
        return _to_entity(row)

    async def get(self, batch_id: uuid.UUID) -> BatchEntity | None:
        row = await self._session.get(Batch, batch_id)
        return _to_entity(row) if row else None

    async def update(self, batch_id: uuid.UUID, **fields: Any) -> None:
        fields["updated_at"] = func.now()
        await self._session.execute(update(Batch).where(Batch.id == batch_id).values(**fields))
        await self._session.commit()

    async def increment_counters(
        self, batch_id: uuid.UUID, *, completed_delta: int = 0, failed_delta: int = 0
    ) -> None:
        await self._session.execute(
            update(Batch)
            .where(Batch.id == batch_id)
            .values(
                completed_jobs=Batch.completed_jobs + completed_delta,
                failed_jobs=Batch.failed_jobs + failed_delta,
                updated_at=func.now(),
            )
        )
        await self._session.commit()

    async def recompute_job_counts(self, batch_id: uuid.UUID) -> tuple[int, int]:
        result = await self._session.execute(
            select(Job.stage, func.count()).where(Job.batch_id == batch_id).group_by(Job.stage)
        )
        counts: dict[str, int] = dict(result.all())  # type: ignore[arg-type]
        completed = int(counts.get("completed", 0))
        failed = int(counts.get("failed", 0))
        return completed, failed
