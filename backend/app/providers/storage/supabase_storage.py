import asyncio

from supabase import Client, create_client


class SupabaseStorageProvider:
    """Wraps supabase-py's storage client. The underlying storage3 client is
    synchronous, so every call is offloaded to a thread via `asyncio.to_thread`
    to avoid blocking the event loop."""

    def __init__(self, url: str, service_role_key: str) -> None:
        self._client: Client = create_client(url, service_role_key)

    async def upload(self, bucket: str, path: str, data: bytes, content_type: str) -> None:
        def _upload() -> None:
            self._client.storage.from_(bucket).upload(
                path,
                data,
                file_options={"content-type": content_type, "upsert": "true"},
            )

        await asyncio.to_thread(_upload)

    async def download(self, bucket: str, path: str) -> bytes:
        def _download() -> bytes:
            return self._client.storage.from_(bucket).download(path)

        return await asyncio.to_thread(_download)

    async def get_signed_url(self, bucket: str, path: str, expires_in: int = 3600) -> str:
        def _sign() -> str:
            result = self._client.storage.from_(bucket).create_signed_url(path, expires_in)
            signed_url = result.get("signedURL") or result.get("signed_url")
            if not signed_url:
                raise RuntimeError(f"Supabase did not return a signed URL for {bucket}/{path}: {result}")
            return str(signed_url)

        return await asyncio.to_thread(_sign)
