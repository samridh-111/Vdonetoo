from fastapi import APIRouter

from app.api.routers import batch, languages, upload, voices

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(upload.router)
api_router.include_router(batch.router)
api_router.include_router(voices.router)
api_router.include_router(languages.router)
