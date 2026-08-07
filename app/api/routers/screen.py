"""
Screen Router

This module defines the stock screening endpoint (``POST /screen``).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies.services import get_screen_service
from app.schemas.analysis import ScreenRequest
from app.schemas.base import APIResponse
from app.schemas.responses import ScreenResponseData
from app.services.screen_service import ScreenService

router = APIRouter(prefix="/screen", tags=["Screen"])


@router.post(
    "",
    response_model=APIResponse[ScreenResponseData],
    summary="Screen companies",
    description="Screens a candidate company against financial health and valuation criteria.",
)
async def screen(
    request: ScreenRequest,
    service: ScreenService = Depends(get_screen_service),
) -> APIResponse[ScreenResponseData]:
    """
    Screen endpoint.

    Args:
        request: The validated screen request.
        service: Injected ``ScreenService`` instance.

    Returns:
        An ``APIResponse`` containing the screening results.
    """
    result = service.screen(request)

    return APIResponse.success_response(
        message=f"Screening completed with {result.total} results",
        data=result,
    )