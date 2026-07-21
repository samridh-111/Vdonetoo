from pydantic import BaseModel, Field


class ParsedScriptRow(BaseModel):
    row_index: int
    external_id: str | None = None
    title: str | None = None
    script_text: str
    notes: str | None = None
    language_hint: str | None = None
    voice_hint: str | None = None
    detected_language_code: str | None = None
    is_valid: bool = True
    validation_error: str | None = None


class ColumnDetection(BaseModel):
    id: str | None = None
    title: str | None = None
    script: str | None = None
    language: str | None = None
    voice: str | None = None
    notes: str | None = None


class UploadRequest(BaseModel):
    google_sheet_url: str | None = Field(default=None, description="Public 'anyone with link' Google Sheets URL")


class UploadResponse(BaseModel):
    upload_token: str
    columns_detected: ColumnDetection
    rows: list[ParsedScriptRow]
    total_rows: int
    valid_rows: int
    warnings: list[str] = Field(default_factory=list)
