from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.deps import RedisDep, get_language_detection_service, get_upload_service
from app.schemas.upload import ColumnDetection, UploadResponse
from app.services.language_detection_service import LanguageDetectionService
from app.services.upload_service import UploadService, UploadValidationError

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", response_model=UploadResponse)
async def upload_batch_source(
    upload_service: Annotated[UploadService, Depends(get_upload_service)],
    language_detection_service: Annotated[LanguageDetectionService, Depends(get_language_detection_service)],
    redis: RedisDep,
    file: UploadFile | None = File(default=None),
    google_sheet_url: str | None = Form(default=None),
) -> UploadResponse:
    if file is None and not google_sheet_url:
        raise HTTPException(422, "Provide either a file upload or a google_sheet_url.")

    try:
        if file is not None:
            content = await file.read()
            df, source_type = await upload_service.parse_file(file.filename or "upload.csv", content)
            source_filename, source_url = file.filename, None
        else:
            assert google_sheet_url is not None
            df = await upload_service.parse_google_sheet(google_sheet_url)
            source_type, source_filename, source_url = "google_sheet", None, google_sheet_url

        columns = upload_service.detect_columns(df)
        rows = upload_service.to_rows(df, columns)
    except UploadValidationError as exc:
        raise HTTPException(422, str(exc)) from exc

    warnings: list[str] = []
    for field in ("id", "title", "voice", "notes"):
        if columns.get(field) is None:
            warnings.append(f"No '{field.title()}' column detected -- values will be left blank.")
    if columns.get("language") is None:
        warnings.append("No 'Language' column detected -- language will be auto-detected from script text.")

    for row in rows:
        if row.is_valid:
            row.detected_language_code = await language_detection_service.resolve(row.script_text, row.language_hint)

    token = await upload_service.stash(
        redis,
        rows=rows,
        source_type=source_type,
        source_filename=source_filename,
        source_url=source_url,
    )

    return UploadResponse(
        upload_token=token,
        columns_detected=ColumnDetection(**columns),
        rows=rows,
        total_rows=len(rows),
        valid_rows=sum(1 for row in rows if row.is_valid),
        warnings=warnings,
    )
