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

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Path

from app.api.dependencies.services import get_company_service
from app.schemas.base import APIResponse
from app.schemas.responses import CompanyData
from app.services.company_service import CompanyService
from app.utils.tickers import normalize_ticker

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

    The hybrid path parameter is validated and normalized via the canonical
    validator before reaching the service, so malicious strings are rejected
    here with a normal 422 client error rather than leaking downstream.

    Args:
        ticker: The ticker symbol from the URL path.
        service: Injected ``CompanyService`` instance.

    Returns:
        An ``APIResponse`` containing the company profile.
    """
    try:
        symbol = normalize_ticker(ticker)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid ticker symbol.")

    result = await asyncio.to_thread(service.get_company, symbol)

    return APIResponse.success_response(
        message=f"Company profile retrieved for {symbol}",
        data=result,
    )