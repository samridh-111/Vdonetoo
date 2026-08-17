import httpx

# MyMemory (like the OpenAI/Gemini providers) is called with human-readable
# language names per the TranslationProvider interface, but its API takes
# ISO 639-1 codes -- this reverse-maps just the languages our own registry
# seeds. See lingva note below for why this provider exists at all.
_NAME_TO_ISO = {
    "english": "en",
    "hindi": "hi",
    "tamil": "ta",
    "kannada": "kn",
    "malayalam": "ml",
    "marathi": "mr",
    "telugu": "te",
    "bengali": "bn",
    "gujarati": "gu",
    "punjabi": "pa",
}

_API_URL = "https://api.mymemory.translated.net/get"


class MyMemoryTranslationProvider:
    """Free, keyless translation via MyMemory's public API -- a quick,
    no-billing stand-in while OpenAI/Gemini billing gets sorted out, not a
    long-term replacement. Anonymous usage is capped at ~5000 chars/day;
    pass a contact_email to raise that to ~50000 chars/day per MyMemory's
    terms (their `de=` param)."""

    def __init__(self, contact_email: str | None = None) -> None:
        self._contact_email = contact_email or None

    async def translate(self, text: str, source_language: str, target_language: str) -> str:
        source_code = _NAME_TO_ISO.get(source_language.lower(), "en")
        target_code = _NAME_TO_ISO.get(target_language.lower())
        if target_code is None:
            raise ValueError(f"MyMemory provider has no ISO mapping for language: {target_language!r}")

        params = {"q": text, "langpair": f"{source_code}|{target_code}"}
        if self._contact_email:
            params["de"] = self._contact_email

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(_API_URL, params=params)
            response.raise_for_status()
            data = response.json()

        if data.get("quotaFinished"):
            raise RuntimeError("MyMemory's free daily translation quota has been used up for this IP/email.")

        return str(data["responseData"]["translatedText"]).strip()
