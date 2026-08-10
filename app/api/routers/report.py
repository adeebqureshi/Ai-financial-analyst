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
from app.schemas.base import APIResponse
from app.schemas.responses import ReportData
from app.services.report_service import ReportService

router = APIRouter(prefix="/report", tags=["Report"])


class ReportTickerRequest(BaseModel):
    """
    Frontend payload for ``POST /report``.

    The frontend only supplies a ticker and an optional query; the full
    analysis inputs are built server-side from real company-specific data.
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
    result = service.generate_ticker_report(
        ticker=payload.ticker,
        query=payload.query,
    )

    return APIResponse.success_response(
        message=f"Report generated for {result.ticker}",
        data=result,
    )
