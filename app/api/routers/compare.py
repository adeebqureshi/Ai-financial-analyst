"""
Compare Router

This module defines the company comparison endpoint (``POST /compare``).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies.services import get_compare_service
from app.schemas.analysis import CompareRequest
from app.schemas.base import APIResponse
from app.schemas.responses import CompareResponseData
from app.services.compare_service import CompareService

router = APIRouter(prefix="/compare", tags=["Compare"])


@router.post(
    "",
    response_model=APIResponse[CompareResponseData],
    summary="Compare companies",
    description="Compares multiple companies using the same financial statement and valuation parameters.",
)
async def compare(
    request: CompareRequest,
    service: CompareService = Depends(get_compare_service),
) -> APIResponse[CompareResponseData]:
    """
    Compare endpoint.

    Args:
        request: The validated compare request.
        service: Injected ``CompareService`` instance.

    Returns:
        An ``APIResponse`` containing the comparison results.
    """
    result = service.compare(request)

    return APIResponse.success_response(
        message=f"Comparison completed for {len(result.results)} tickers",
        data=result,
    )