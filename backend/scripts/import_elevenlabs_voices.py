"""One-off / re-runnable import: pulls every voice from the configured
ElevenLabs account and upserts it into the `voices` table, so the real
account's trained/professional voices show up in the Voice Selection panel
instead of (or alongside) the generic seed presets.

Usage: python scripts/import_elevenlabs_voices.py
"""

import asyncio
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import new_worker_session
from app.models import Voice

# ElevenLabs label language -> our `languages` registry code. Anything not
# listed here (e.g. 'ja', 'de', 'fr', 'pt') is imported with language_code
# left null, since our `languages` table only covers these 10.
_LANGUAGE_MAP = {
    "en": "en",
    "hi": "hi",
    "ta": "ta",
    "kn": "kn",
    "ml": "ml",
    "mr": "mr",
    "te": "te",
    "bn": "bn",
    "gu": "gu",
    "pa": "pa",
}


def _slugify(name: str, voice_id: str, existing: set[str]) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    slug = slug or "voice"
    if slug not in existing:
        return slug
    return f"{slug}_{voice_id[:6].lower()}"


async def _fetch_all_voices(api_key: str) -> list[dict[str, Any]]:
    remote_voices: list[dict[str, Any]] = []
    next_page_token: str | None = None

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            params: dict[str, Any] = {"page_size": 100}
            if next_page_token:
                params["next_page_token"] = next_page_token
            response = await client.get(
                "https://api.elevenlabs.io/v2/voices",
                params=params,
                headers={"xi-api-key": api_key},
            )
            response.raise_for_status()
            page = response.json()
            remote_voices.extend(page["voices"])
            if not page.get("has_more"):
                break
            next_page_token = page.get("next_page_token")

    return remote_voices


async def main() -> None:
    settings = get_settings()
    remote_voices = await _fetch_all_voices(settings.elevenlabs_api_key)

    async with new_worker_session() as session:
        existing_result = await session.execute(select(Voice))
        existing_rows = {row.elevenlabs_voice_id: row for row in existing_result.scalars().all()}
        existing_preset_keys = {row.preset_key for row in existing_rows.values()}

        created, updated = 0, 0
        for entry in remote_voices:
            voice_id = entry["voice_id"]
            name = entry["name"]
            language_label: str | None = (entry.get("labels") or {}).get("language")
            language_code = _LANGUAGE_MAP.get(language_label) if language_label else None

            if voice_id in existing_rows:
                row = existing_rows[voice_id]
                row.name = name
                row.language_code = language_code
                row.is_active = True
                updated += 1
                continue

            preset_key = _slugify(name, voice_id, existing_preset_keys)
            existing_preset_keys.add(preset_key)
            session.add(
                Voice(
                    name=name,
                    preset_key=preset_key,
                    elevenlabs_voice_id=voice_id,
                    language_code=language_code,
                    similarity=0.75,
                    stability=0.5,
                    style=0.0,
                    speed=1.0,
                    is_active=True,
                )
            )
            created += 1

        # Retire the generic stock-voice seed presets now that real trained
        # voices are available -- kept in the DB (not deleted) in case
        # anything still references them, just hidden from the picker.
        stock_preset_keys = [
            "vedantu_female",
            "vedantu_male",
            "teacher_female",
            "teacher_male",
            "parent_female",
            "parent_male",
            "friendly",
            "professional",
        ]
        stock_result = await session.execute(select(Voice).where(Voice.preset_key.in_(stock_preset_keys)))
        retired = 0
        for row in stock_result.scalars().all():
            row.is_active = False
            retired += 1

        await session.commit()

    print(f"Imported {created} new voices, updated {updated} existing, retired {retired} stock presets.")


if __name__ == "__main__":
    asyncio.run(main())
