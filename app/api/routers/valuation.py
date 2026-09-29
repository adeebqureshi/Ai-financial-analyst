from __future__ import annotations
import asyncio
from fastapi import APIRouter, Depends
from app.api.dependencies.services import get_valuation_service
from app.schemas.analysis import ValuationRequest
from app.schemas.base import APIResponse
from app.schemas.responses import ValuationResponseData
from app.services.valuation_service import ValuationService
router = APIRouter(tags=["Valuation"])
@router.post(
    "/valuation",
    response_model=APIResponse[ValuationResponseData],
    summary="Run DCF valuation",
    description="Runs a Discounted Cash Flow (DCF) valuation for a company.",
)
async def valuate(
    request: ValuationRequest,
    service: ValuationService = Depends(get_valuation_service),
) -> APIResponse[ValuationResponseData]:
    result = await asyncio.to_thread(service.valuate, request)
    return APIResponse.success_response(
        message="Valuation completed",
        data=result,
    )
