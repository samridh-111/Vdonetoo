import uuid
from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from app.api.deps import RedisDep, get_batch_service
from app.schemas.batch import (
    BatchCreateRequest,
    BatchCreateResponse,
    BatchDetail,
    BatchEstimateResponse,
    BatchIdRequest,
    BatchStatusOut,
    BatchSummary,
)
from app.services.batch_service import BatchNotFoundError, BatchService, BatchStateError
from app.services.upload_service import UploadValidationError

router = APIRouter(prefix="/batch", tags=["batch"])

BatchServiceDep = Annotated[BatchService, Depends(get_batch_service)]


@router.post("/create", response_model=BatchCreateResponse)
async def create_batch(
    request: BatchCreateRequest, batch_service: BatchServiceDep, redis: RedisDep
) -> BatchCreateResponse:
    try:
        batch = await batch_service.create_batch(redis, request)
    except UploadValidationError as exc:
        raise HTTPException(422, str(exc)) from exc

    return BatchCreateResponse(batch_id=batch.id, status=batch.status, total_scripts=batch.total_scripts)  # type: ignore[arg-type]


@router.post("/start", response_model=BatchSummary)
async def start_batch(request: BatchIdRequest, batch_service: BatchServiceDep) -> BatchSummary:
    try:
        batch = await batch_service.start_batch(request.batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except BatchStateError as exc:
        raise HTTPException(409, str(exc)) from exc

    return BatchSummary(**asdict(batch))


@router.post("/cancel", response_model=BatchSummary)
async def cancel_batch(request: BatchIdRequest, batch_service: BatchServiceDep) -> BatchSummary:
    try:
        batch = await batch_service.cancel_batch(request.batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except BatchStateError as exc:
        raise HTTPException(409, str(exc)) from exc

    return BatchSummary(**asdict(batch))


@router.get("/estimate", response_model=BatchEstimateResponse)
async def estimate_batch(
    batch_service: BatchServiceDep, script_count: int, language_count: int = 1
) -> BatchEstimateResponse:
    # Registered before /{batch_id} -- a static path must come first, or
    # Starlette would match "estimate" as a batch_id (and fail UUID parsing)
    # since path routing is structural, not type-aware.
    return await batch_service.estimate(script_count, language_count)


@router.get("/{batch_id}", response_model=BatchDetail)
async def get_batch(batch_id: uuid.UUID, batch_service: BatchServiceDep) -> BatchDetail:
    try:
        return await batch_service.get_batch_detail(batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/{batch_id}/status", response_model=BatchStatusOut)
async def get_batch_status(batch_id: uuid.UUID, batch_service: BatchServiceDep) -> BatchStatusOut:
    try:
        return await batch_service.get_batch_status(batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/{batch_id}/download")
async def download_batch(batch_id: uuid.UUID, batch_service: BatchServiceDep) -> RedirectResponse:
    try:
        signed_url = await batch_service.get_download_url(batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except BatchStateError as exc:
        raise HTTPException(409, str(exc)) from exc

    return RedirectResponse(url=signed_url, status_code=302)
