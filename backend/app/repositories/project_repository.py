import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import ProjectEntity
from app.models import Project


def _to_entity(row: Project) -> ProjectEntity:
    return ProjectEntity(
        id=row.id,
        name=row.name,
        description=row.description,
        module=row.module,
        created_by=row.created_by,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, project_id: uuid.UUID) -> ProjectEntity | None:
        row = await self._session.get(Project, project_id)
        return _to_entity(row) if row else None

    async def get_or_create_default(self, module: str, name: str) -> ProjectEntity:
        result = await self._session.execute(
            select(Project).where(Project.module == module).order_by(Project.created_at).limit(1)
        )
        row = result.scalar_one_or_none()
        if row is not None:
            return _to_entity(row)

        row = Project(name=name, module=module)
        self._session.add(row)
        await self._session.flush()
        await self._session.commit()
        return _to_entity(row)
