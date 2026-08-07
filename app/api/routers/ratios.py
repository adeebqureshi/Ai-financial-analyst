"""
Ratios Router

This module defines the financial ratios endpoint (``POST /financial-ratios``).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies.services import get_ratios_service
from app.schemas.analysis import FinancialRatiosRequest
from app.schemas.base import APIResponse
from app.schemas.responses import FinancialRatiosData
from app.services.ratios_service import RatiosService

router = APIRouter(prefix="/financial-ratios", tags=["Financial Ratios"])


@router.post(
    "",
    response_model=APIResponse[FinancialRatiosData],
    summary="Compute financial ratios",
    description="Computes key financial ratios from a financial statement.",
)
async def financial_ratios(
    request: FinancialRatiosRequest,
    service: RatiosService = Depends(get_ratios_service),
) -> APIResponse[FinancialRatiosData]:
    """
    Financial ratios endpoint.

    Args:
        request: The validated ratios request.
        service: Injected ``RatiosService`` instance.

    Returns:
        An ``APIResponse`` containing the computed ratios.
    """
    result = service.compute(request)

    return APIResponse.success_response(
        message="Financial ratios computed",
        data=result,
    )