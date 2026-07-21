from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import LanguageEntity
from app.models import Language


def _to_entity(row: Language) -> LanguageEntity:
    return LanguageEntity(
        code=row.code,
        name=row.name,
        locale=row.locale,
        detector_aliases=list(row.detector_aliases or []),
        header_synonyms=list(row.header_synonyms or []),
        is_active=row.is_active,
        created_at=row.created_at,
    )


class SqlLanguageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[LanguageEntity]:
        result = await self._session.execute(
            select(Language).where(Language.is_active.is_(True)).order_by(Language.name)
        )
        return [_to_entity(row) for row in result.scalars().all()]

    async def get(self, code: str) -> LanguageEntity | None:
        row = await self._session.get(Language, code)
        return _to_entity(row) if row else None

    async def resolve_detector_alias(self, alias: str) -> LanguageEntity | None:
        result = await self._session.execute(
            select(Language).where(Language.detector_aliases.any(alias.lower()))  # type: ignore[arg-type]
        )
        row = result.scalars().first()
        return _to_entity(row) if row else None

    async def resolve_header_synonym(self, token: str) -> LanguageEntity | None:
        result = await self._session.execute(
            select(Language).where(Language.header_synonyms.any(token.strip().lower()))  # type: ignore[arg-type]
        )
        row = result.scalars().first()
        return _to_entity(row) if row else None
