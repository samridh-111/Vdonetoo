import io
import json
import re
import secrets
from dataclasses import dataclass

import httpx
import pandas as pd
from rapidfuzz import fuzz, process
from redis.asyncio import Redis

from app.schemas.upload import ParsedScriptRow

_UPLOAD_STASH_TTL_SECONDS = 30 * 60
_UPLOAD_STASH_PREFIX = "upload_stash:"


@dataclass(frozen=True, slots=True)
class UploadStashPayload:
    rows: list[ParsedScriptRow]
    source_type: str
    source_filename: str | None
    source_url: str | None

# Column-header synonyms: matching *which column* is the Script/Language/etc.
# column. This is UI header-matching, not core business logic, so a
# hardcoded synonym list is acceptable here (unlike language detection
# itself, which is registry-driven -- see app/providers/language/detector.py
# and the `languages.header_synonyms` column, which instead matches the
# *value* of a Language column cell to a language code).
_COLUMN_SYNONYMS: dict[str, list[str]] = {
    "id": ["id", "scriptid", "script id", "sno", "sr no", "#", "row id"],
    "title": ["title", "name", "script title", "label", "heading"],
    "script": ["script", "text", "script text", "content", "message", "dialogue", "prompt"],
    "language": ["language", "lang", "target language", "locale"],
    "voice": ["voice", "voice preset", "voice name", "speaker"],
    "notes": ["notes", "note", "comment", "comments", "remarks", "description"],
}

_GOOGLE_SHEET_ID_PATTERN = re.compile(r"/spreadsheets/d/([a-zA-Z0-9-_]+)")
_GOOGLE_SHEET_GID_PATTERN = re.compile(r"[?&#]gid=([0-9]+)")

_FUZZY_MATCH_THRESHOLD = 80


class UploadValidationError(Exception):
    pass


class UploadService:
    async def parse_file(self, filename: str, content: bytes) -> tuple[pd.DataFrame, str]:
        lower = filename.lower()
        if lower.endswith(".csv"):
            return pd.read_csv(io.BytesIO(content)), "csv"
        if lower.endswith(".xlsx"):
            return pd.read_excel(io.BytesIO(content)), "xlsx"
        raise UploadValidationError("Unsupported file type. Upload a .csv or .xlsx file.")

    async def parse_google_sheet(self, sheet_url: str) -> pd.DataFrame:
        id_match = _GOOGLE_SHEET_ID_PATTERN.search(sheet_url)
        if not id_match:
            raise UploadValidationError("Could not parse a spreadsheet ID from that Google Sheets URL.")

        sheet_id = id_match.group(1)
        gid_match = _GOOGLE_SHEET_GID_PATTERN.search(sheet_url)
        gid = gid_match.group(1) if gid_match else "0"
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(export_url)

        content_type = response.headers.get("content-type", "")
        if response.status_code != 200 or "text/csv" not in content_type:
            raise UploadValidationError(
                "Could not fetch that Google Sheet. Make sure it's shared as "
                "'Anyone with the link can view'."
            )
        return pd.read_csv(io.StringIO(response.text))

    def detect_columns(self, df: pd.DataFrame) -> dict[str, str | None]:
        normalized = {str(col).strip().lower(): col for col in df.columns}
        candidates = list(normalized.keys())
        detected: dict[str, str | None] = {}

        for field, synonyms in _COLUMN_SYNONYMS.items():
            match: str | None = None
            for synonym in synonyms:
                if synonym in normalized:
                    match = normalized[synonym]
                    break

            if match is None and candidates:
                for synonym in synonyms:
                    best = process.extractOne(
                        synonym, candidates, scorer=fuzz.WRatio, score_cutoff=_FUZZY_MATCH_THRESHOLD
                    )
                    if best:
                        match = normalized[best[0]]
                        break

            detected[field] = match

        return detected

    def to_rows(self, df: pd.DataFrame, columns: dict[str, str | None]) -> list[ParsedScriptRow]:
        if columns.get("script") is None:
            raise UploadValidationError(
                "Could not detect a Script column. Rename the column containing "
                "the script text to 'Script' and re-upload."
            )

        def cell(record: dict[str, object], field: str) -> str | None:
            column = columns.get(field)
            if column is None:
                return None
            value = record.get(column)
            if value is None or (isinstance(value, float) and pd.isna(value)):
                return None
            text = str(value).strip()
            return text or None

        rows: list[ParsedScriptRow] = []
        for idx, record in enumerate(df.to_dict(orient="records")):
            script_text = cell(record, "script") or ""
            is_valid = bool(script_text.strip())
            rows.append(
                ParsedScriptRow(
                    row_index=idx,
                    external_id=cell(record, "id"),
                    title=cell(record, "title"),
                    script_text=script_text,
                    notes=cell(record, "notes"),
                    language_hint=cell(record, "language"),
                    voice_hint=cell(record, "voice"),
                    is_valid=is_valid,
                    validation_error=None if is_valid else "Script text is empty.",
                )
            )
        return rows

    async def stash(
        self,
        redis: Redis,
        *,
        rows: list[ParsedScriptRow],
        source_type: str,
        source_filename: str | None,
        source_url: str | None,
    ) -> str:
        """Parsed rows aren't persisted until POST /batch/create (the user
        may still tweak translation mode/voices in the preview UI first), so
        they're stashed in Redis under a short-lived token instead."""
        token = secrets.token_urlsafe(24)
        payload = {
            "rows": [row.model_dump(mode="json") for row in rows],
            "source_type": source_type,
            "source_filename": source_filename,
            "source_url": source_url,
        }
        await redis.set(f"{_UPLOAD_STASH_PREFIX}{token}", json.dumps(payload), ex=_UPLOAD_STASH_TTL_SECONDS)
        return token

    async def unstash(self, redis: Redis, token: str) -> UploadStashPayload:
        raw = await redis.get(f"{_UPLOAD_STASH_PREFIX}{token}")
        if raw is None:
            raise UploadValidationError("This upload has expired. Please upload the file again.")
        payload = json.loads(raw)
        return UploadStashPayload(
            rows=[ParsedScriptRow.model_validate(row) for row in payload["rows"]],
            source_type=payload["source_type"],
            source_filename=payload["source_filename"],
            source_url=payload["source_url"],
        )
