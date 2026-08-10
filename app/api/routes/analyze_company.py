"""
Analyze Company Route

This module defines the frontend analysis endpoint (``POST /analyze-company``)
which performs a comprehensive AI-driven financial analysis of a company using
real, company-specific financial data.

Design Decisions:
    - **No business logic in route**: The route handler delegates entirely
      to ``AnalysisService.analyze_ticker()``, the same Phase 2 entry point
      used by ``POST /analyze``.
    - **No duplicated data**: The route does not fabricate or hardcode any
      financial figures; the service fetches the real financial statements,
      market data and risk scores for the requested ticker.
    - **Dependency injection**: ``AnalysisService`` is injected via
      ``Depends(get_analysis_service)``, making it overridable in tests.
    - **Standard response format**: Returns ``APIResponse[AnalyzeResponseData]``
      for consistency with all other endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from app.api.dependencies.services import get_analysis_service
from app.schemas.base import APIResponse
from app.schemas.responses import AnalyzeResponseData
from app.services.analysis_service import AnalysisService

router = APIRouter(
    prefix="/analyze-company",
    tags=["Frontend"],
)


class AnalyzeCompanyRequest(BaseModel):
    """
    Frontend payload for ``POST /analyze-company``.

    The frontend only supplies a ticker; the full analysis inputs are
    built server-side from real company-specific financial data.
    """

    ticker: str = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Ticker symbol (1-5 letters).",
    )
    query: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional analysis query.",
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
    response_model=APIResponse[AnalyzeResponseData],
    summary="Analyze a company",
    description=(
        "Performs a comprehensive AI-driven financial analysis of a company "
        "using real company-specific financial statements, market data, "
        "valuation, financial health, and an investment recommendation."
    ),
)
async def analyze_company(
    payload: AnalyzeCompanyRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> APIResponse[AnalyzeResponseData]:
    """
    Frontend entrypoint.

    Args:
        payload: The frontend payload containing the ticker.
        service: Injected ``AnalysisService`` instance.

    Returns:
        An ``APIResponse`` containing the analysis results.
    """
    result = service.analyze_ticker(
        ticker=payload.ticker,
        query=payload.query,
    )

    return APIResponse.success_response(
        message=f"Analysis completed for {result.ticker}",
        data=result,
    )
