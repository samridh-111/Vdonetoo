from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers.ws import router as ws_router
from app.api.v1_router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.environment)

app = FastAPI(title="Internal Automation Hub -- Batch IVR Automation", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.next_public_api_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(ws_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
