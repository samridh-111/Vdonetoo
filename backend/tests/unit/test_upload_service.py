import pandas as pd
import pytest

from app.services.upload_service import UploadService, UploadValidationError


@pytest.fixture
def service() -> UploadService:
    return UploadService()


def test_detect_columns_exact_match_case_insensitive(service: UploadService) -> None:
    df = pd.DataFrame(columns=["ID", "Title", "Script", "Language", "Voice", "Notes"])
    columns = service.detect_columns(df)
    assert columns == {
        "id": "ID",
        "title": "Title",
        "script": "Script",
        "language": "Language",
        "voice": "Voice",
        "notes": "Notes",
    }


def test_detect_columns_synonyms_and_fuzzy_match(service: UploadService) -> None:
    df = pd.DataFrame(columns=["Script ID", "Script Text", "Target Language", "Voice Preset"])
    columns = service.detect_columns(df)
    assert columns["id"] == "Script ID"
    assert columns["script"] == "Script Text"
    assert columns["language"] == "Target Language"
    assert columns["voice"] == "Voice Preset"
    assert columns["title"] is None
    assert columns["notes"] is None


def test_to_rows_requires_script_column(service: UploadService) -> None:
    df = pd.DataFrame({"Title": ["Greeting"]})
    columns = service.detect_columns(df)
    with pytest.raises(UploadValidationError):
        service.to_rows(df, columns)


def test_to_rows_marks_empty_script_text_invalid(service: UploadService) -> None:
    df = pd.DataFrame(
        {
            "ID": ["001", "002"],
            "Script": ["Welcome to support.", "   "],
            "Language": ["English", None],
        }
    )
    columns = service.detect_columns(df)
    rows = service.to_rows(df, columns)

    assert len(rows) == 2
    assert rows[0].is_valid is True
    assert rows[0].external_id == "001"
    assert rows[0].language_hint == "English"
    assert rows[1].is_valid is False
    assert rows[1].validation_error == "Script text is empty."


async def test_parse_google_sheet_rejects_unparseable_url(service: UploadService) -> None:
    with pytest.raises(UploadValidationError):
        await service.parse_google_sheet("https://example.com/not-a-sheet")
