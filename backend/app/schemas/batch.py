import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.script import ScriptOut


class BatchIdRequest(BaseModel):
    batch_id: uuid.UUID


class TranslationMode(StrEnum):
    KEEP_ORIGINAL = "keep_original"
    TRANSLATE_EVERYTHING = "translate_everything"
    TRANSLATE_SELECTED = "translate_selected"
    GENERATE_MULTIPLE = "generate_multiple"


class TranslationProviderName(StrEnum):
    OPENAI = "openai"
    GEMINI = "gemini"
    MYMEMORY = "mymemory"


class BatchStatusName(StrEnum):
    DRAFT = "draft"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchCreateRequest(BaseModel):
    upload_token: str
    name: str
    translation_mode: TranslationMode
    target_languages: list[str] = Field(default_factory=list)
    # None (not sent) means "use whatever TRANSLATION_PROVIDER is configured
    # in the backend's .env" -- there's no UI picker for this yet, so the
    # frontend must never hardcode a provider here (it did, which is why
    # switching the backend to Gemini had no effect until this was fixed).
    translation_provider: TranslationProviderName | None = None
    default_voice_map: dict[str, str] = Field(default_factory=dict, description="language_code -> voice preset_key or id")
    concurrency_limit: int = 8


class BatchCreateResponse(BaseModel):
    batch_id: uuid.UUID
    status: BatchStatusName
    total_scripts: int


class BatchSummary(BaseModel):
    id: uuid.UUID
    name: str
    status: BatchStatusName
    total_scripts: int
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class BatchDetail(BatchSummary):
    source_type: str
    translation_mode: str
    target_languages: list[str]
    translation_provider: str
    zip_storage_path: str | None
    scripts: list[ScriptOut] = []


class BatchStatusOut(BaseModel):
    id: uuid.UUID
    status: BatchStatusName
    total_scripts: int
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    percent_complete: float
    estimated_seconds_remaining: float | None
    scripts: list[ScriptOut] = []


class BatchEstimateResponse(BaseModel):
    total_jobs: int
    estimated_seconds: float
    based_on_historical_data: bool
