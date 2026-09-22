from __future__ import annotations
import asyncio
from fastapi import APIRouter, Depends
from app.api.dependencies.services import get_health_service
from app.schemas.base import APIResponse
from app.schemas.health import HealthResponse
from app.services.health_service import HealthService
router = APIRouter(prefix="/health", tags=["Health"])
@router.get(
    "",
    response_model=APIResponse[HealthResponse],
    summary="Health check",
    description="Returns the health status of the application and its components.",
)
async def health_check(
    service: HealthService = Depends(get_health_service),
) -> APIResponse[HealthResponse]:
    health_data = await asyncio.to_thread(service.check_health)
    return APIResponse.success_response(
        message="Health check completed",
        data=health_data,
    )