"""
Compare Router

This module defines the company comparison endpoint (``POST /compare``).

The frontend only supplies a list of tickers; the full ``CompareRequest``
is built internally from default analysis inputs, mirroring the contract
used by ``POST /analyze`` (``AnalyzeTickerRequest``).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from app.api.dependencies.services import get_compare_service
from app.schemas.analysis import (
    CompareRequest,
    FinancialStatementInput,
    ValuationParams,
)
from app.schemas.base import APIResponse
from app.schemas.responses import CompareResponseData
from app.services.compare_service import CompareService

router = APIRouter(prefix="/compare", tags=["Compare"])


class CompareTickersRequest(BaseModel):
    """
    Frontend payload for ``POST /compare``.

    The frontend only supplies tickers; the full ``CompareRequest`` is
    built internally from default analysis inputs.
    """

    tickers: list[str] = Field(
        ...,
        min_length=2,
        max_length=10,
        description="List of 2-10 ticker symbols to compare.",
    )

    @field_validator("tickers")
    @classmethod
    def validate_ticker_list(cls, v: list[str]) -> list[str]:
        """Normalize, validate, and de-duplicate the ticker list."""
        seen: set[str] = set()
        result: list[str] = []
        for raw in v:
            ticker = raw.strip().upper()
            if not (1 <= len(ticker) <= 5) or not ticker.isalpha():
                raise ValueError("Ticker must be 1-5 uppercase letters (e.g., 'AAPL').")
            if ticker not in seen:
                seen.add(ticker)
                result.append(ticker)
        if len(result) < 2:
            raise ValueError("At least 2 distinct tickers are required.")
        return result


@router.post(
    "",
    response_model=APIResponse[CompareResponseData],
    summary="Compare companies",
    description="Compares multiple companies using the same financial statement and valuation parameters.",
)
async def compare(
    payload: CompareTickersRequest,
    service: CompareService = Depends(get_compare_service),
) -> APIResponse[CompareResponseData]:
    """
    Compare endpoint.

    Args:
        payload: The frontend payload containing only the tickers.
        service: Injected ``CompareService`` instance.

    Returns:
        An ``APIResponse`` containing the comparison results.
    """
    request = CompareRequest(
        tickers=payload.tickers,
        statement=FinancialStatementInput(
            revenue=394_328.0,
            operating_income=114_301.0,
            net_income=96_995.0,
            total_assets=352_583.0,
            total_liabilities=279_486.0,
            cash=30_545.0,
            debt=111_088.0,
            shares_outstanding=15_431.0,
            free_cash_flow=99_584.0,
        ),
        valuation=ValuationParams(
            current_price=191.58,
            growth_rate=0.08,
            risk_free_rate=0.0425,
            beta=1.24,
            market_return=0.10,
            tax_rate=0.21,
        ),
    )

    result = service.compare(request)

    return APIResponse.success_response(
        message=f"Comparison completed for {len(result.results)} tickers",
        data=result,
    )
