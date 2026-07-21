from pydantic import BaseModel


class LanguageOut(BaseModel):
    code: str
    name: str
    locale: str | None
    is_active: bool

    model_config = {"from_attributes": True}
