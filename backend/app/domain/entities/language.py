from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class LanguageEntity:
    code: str
    name: str
    locale: str | None
    detector_aliases: list[str] = field(default_factory=list)
    header_synonyms: list[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime | None = None
