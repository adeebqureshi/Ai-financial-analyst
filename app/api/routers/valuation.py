from __future__ import annotations
import asyncio
from fastapi import APIRouter, Depends
from app.api.dependencies.services import get_valuation_service
from app.schemas.analysis import IntrinsicValueRequest, ValuationRequest
from app.schemas.base import APIResponse
from app.schemas.responses import IntrinsicValueResponseData, ValuationResponseData
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
@router.post(
    "/intrinsic-value",
    response_model=APIResponse[IntrinsicValueResponseData],
    summary="Calculate intrinsic value",
    description="Calculates the intrinsic value per share using DCF analysis.",
)
async def intrinsic_value(
    request: IntrinsicValueRequest,
    service: ValuationService = Depends(get_valuation_service),
) -> APIResponse[IntrinsicValueResponseData]:
    result = await asyncio.to_thread(service.intrinsic_value, request)
    return APIResponse.success_response(
        message="Intrinsic value calculated",
        data=result,
    )