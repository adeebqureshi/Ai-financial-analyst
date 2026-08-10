"""
Report Router

This module defines the report generation endpoint (``POST /report``).

The frontend only supplies a ticker (and optional query); the full
``ReportRequest`` is built internally from default analysis inputs,
mirroring the contract used by ``POST /analyze``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from app.api.dependencies.services import get_report_service
from app.schemas.analysis import (
    FinancialStatementInput,
    ReportRequest,
    ValuationParams,
)
from app.schemas.base import APIResponse
from app.schemas.responses import ReportData
from app.services.report_service import ReportService

router = APIRouter(prefix="/report", tags=["Report"])


class ReportTickerRequest(BaseModel):
    """
    Frontend payload for ``POST /report``.

    The frontend only supplies a ticker and an optional query; the full
    ``ReportRequest`` is built internally from default analysis inputs.
    """

    ticker: str = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Ticker symbol (1-5 letters).",
    )
    query: str = Field(
        default="",
        min_length=0,
        max_length=2000,
        description="Optional report query.",
    )

    @field_validator("ticker")
    @classmethod
    def validate_ticker_symbol(cls, v: str) -> str:
        """Normalize and validate the ticker symbol."""
        ticker = v.strip().upper()
        if not (1 <= len(ticker) <= 5) or not ticker.isalpha():
            raise ValueError("Ticker must be 1-5 uppercase letters (e.g., 'AAPL').")
        return ticker


@router.post(
    "",
    response_model=APIResponse[ReportData],
    summary="Generate a financial report",
    description="Generates a comprehensive LLM-powered financial report for a company.",
)
async def report(
    payload: ReportTickerRequest,
    service: ReportService = Depends(get_report_service),
) -> APIResponse[ReportData]:
    """
    Report endpoint.

    Args:
        payload: The frontend payload containing the ticker.
        service: Injected ``ReportService`` instance.

    Returns:
        An ``APIResponse`` containing the generated report.
    """
    request = ReportRequest(
        ticker=payload.ticker,
        query=payload.query or f"Generate a comprehensive financial report for {payload.ticker}",
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
        piotroski_score=9,
        altman_score=3.5,
        beneish_score=-2.4,
    )

    result = service.generate(request)

    return APIResponse.success_response(
        message=f"Report generated for {request.ticker}",
        data=result,
    )
