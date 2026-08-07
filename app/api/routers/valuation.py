"""
Valuation Router

This module defines the DCF valuation endpoints (``POST /valuation`` and
``POST /intrinsic-value``).

Design Decisions:
    - **No business logic in route**: Route handlers delegate entirely
      to ``ValuationService``.
    - **Dependency injection**: ``ValuationService`` is injected via
      ``Depends(get_valuation_service)``, making it overridable in tests.
    - **Standard response format**: Returns ``APIResponse`` for consistency.
"""

from __future__ import annotations

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
    """
    Valuation endpoint.

    Args:
        request: The validated valuation request.
        service: Injected ``ValuationService`` instance.

    Returns:
        An ``APIResponse`` containing the valuation result.
    """
    result = service.valuate(request)

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
    """
    Intrinsic value endpoint.

    Args:
        request: The validated intrinsic value request.
        service: Injected ``ValuationService`` instance.

    Returns:
        An ``APIResponse`` containing the intrinsic value.
    """
    result = service.intrinsic_value(request)

    return APIResponse.success_response(
        message="Intrinsic value calculated",
        data=result,
    )