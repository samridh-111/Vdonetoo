from google import genai
from google.genai import types

_SYSTEM_INSTRUCTION = (
    "You are a professional translator for an IVR (Interactive Voice "
    "Response) phone system. Translate the given script text from "
    "{source_language} to {target_language}. Preserve the tone, meaning, "
    "and intent exactly as it would be spoken aloud to a caller. Respond "
    "with only the translation itself -- no explanations, no quotation "
    "marks."
)


class GeminiTranslationProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def translate(self, text: str, source_language: str, target_language: str) -> str:
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_INSTRUCTION.format(
                    source_language=source_language, target_language=target_language
                ),
                temperature=0.2,
            ),
        )
        return response.text.strip() if response.text else ""
