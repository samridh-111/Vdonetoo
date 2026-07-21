from typing import Protocol


class StorageProvider(Protocol):
    """Contract for object storage. Concrete implementation:
    app/providers/storage/supabase_storage.py."""

    async def upload(self, bucket: str, path: str, data: bytes, content_type: str) -> None: ...
    async def download(self, bucket: str, path: str) -> bytes: ...
    async def get_signed_url(self, bucket: str, path: str, expires_in: int = 3600) -> str: ...
