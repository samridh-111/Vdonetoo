from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_language_repository
from app.repositories import SqlLanguageRepository
from app.schemas.language import LanguageOut

router = APIRouter(prefix="/languages", tags=["languages"])


@router.get("", response_model=list[LanguageOut])
async def list_languages(
    language_repository: Annotated[SqlLanguageRepository, Depends(get_language_repository)],
) -> list[LanguageOut]:
    languages = await language_repository.list_active()
    return [LanguageOut.model_validate(language) for language in languages]
