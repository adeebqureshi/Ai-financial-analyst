"""
Company Router

This module defines the company profile endpoint (``GET /company/{ticker}``).

Design Decisions:
    - **No business logic in route**: The route handler delegates entirely
      to ``CompanyService.get_company()``.
    - **Dependency injection**: ``CompanyService`` is injected via
      ``Depends(get_company_service)``, making it overridable in tests.
    - **Standard response format**: Returns ``APIResponse[CompanyData]``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path

from app.api.dependencies.services import get_company_service
from app.schemas.base import APIResponse
from app.schemas.responses import CompanyData
from app.services.company_service import CompanyService

router = APIRouter(prefix="/company", tags=["Company"])


@router.get(
    "/{ticker}",
    response_model=APIResponse[CompanyData],
    summary="Get company profile",
    description="Returns the company profile for a given ticker symbol.",
)
async def get_company(
    ticker: str = Path(..., min_length=1, max_length=5, description="Ticker symbol (1-5 letters)."),
    service: CompanyService = Depends(get_company_service),
) -> APIResponse[CompanyData]:
    """
    Company profile endpoint.

    Args:
        ticker: The ticker symbol from the URL path.
        service: Injected ``CompanyService`` instance.

    Returns:
        An ``APIResponse`` containing the company profile.
    """
    result = service.get_company(ticker.upper())

    return APIResponse.success_response(
        message=f"Company profile retrieved for {ticker.upper()}",
        data=result,
    )