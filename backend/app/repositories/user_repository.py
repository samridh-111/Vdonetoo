import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import UserEntity
from app.models import User


def _to_entity(row: User) -> UserEntity:
    return UserEntity(
        id=row.id,
        email=row.email,
        display_name=row.display_name,
        role=row.role,
        created_at=row.created_at,
    )


class SqlUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: uuid.UUID) -> UserEntity | None:
        row = await self._session.get(User, user_id)
        return _to_entity(row) if row else None

    async def get_by_email(self, email: str) -> UserEntity | None:
        result = await self._session.execute(select(User).where(User.email == email))
        row = result.scalar_one_or_none()
        return _to_entity(row) if row else None

    async def create(self, email: str, display_name: str | None = None) -> UserEntity:
        row = User(email=email, display_name=display_name)
        self._session.add(row)
        await self._session.flush()
        await self._session.commit()
        return _to_entity(row)
