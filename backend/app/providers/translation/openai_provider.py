from openai import AsyncOpenAI

_SYSTEM_PROMPT = (
    "You are a professional translator for an IVR (Interactive Voice "
    "Response) phone system. Translate the given script text from "
    "{source_language} to {target_language}. Preserve the tone, meaning, "
    "and intent exactly as it would be spoken aloud to a caller. Do not "
    "add explanations, quotation marks, or any text other than the "
    "translation itself."
)


class OpenAITranslationProvider:
    def __init__(self, api_key: str, model: str) -> None:
        # A batch fans out one translation call per script concurrently, so
        # even a handful of scripts can burst past a low-tier account's
        # requests-per-minute limit. The SDK's built-in retry/backoff
        # (default max_retries=2) isn't enough to ride that out; bump it.
        self._client = AsyncOpenAI(api_key=api_key, max_retries=6)
        self._model = model

    async def translate(self, text: str, source_language: str, target_language: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": _SYSTEM_PROMPT.format(
                        source_language=source_language, target_language=target_language
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""
