"""
Analysis Router

This module defines the analysis endpoint (``POST /analyze``) which performs
a comprehensive AI-driven financial analysis of a company.

Design Decisions:
    - **No business logic in route**: The route handler delegates entirely
      to ``AnalysisService.analyze()``.
    - **Dependency injection**: ``AnalysisService`` is injected via
      ``Depends(get_analysis_service)``, making it overridable in tests.
    - **Standard response format**: Returns ``APIResponse[AnalyzeResponseData]``
      for consistency with all other endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies.services import get_analysis_service
from app.schemas.analysis import (
    AnalyzeRequest,
    FinancialStatementInput,
    ValuationParams,
)
from app.schemas.base import APIResponse
from app.schemas.responses import AnalyzeResponseData
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analyze", tags=["Analysis"])


class AnalyzeTickerRequest(BaseModel):
    """
    Frontend payload for ``POST /analyze``.

    The frontend only supplies a ticker; the full ``AnalyzeRequest`` is
    built internally from placeholder analysis inputs.
    """

    ticker: str = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Ticker symbol (1-5 letters).",
    )


@router.post(
    "",
    response_model=APIResponse[AnalyzeResponseData],
    summary="Analyze a company",
    description=(
        "Performs a comprehensive AI-driven financial analysis of a company "
        "including valuation, financial health, and an investment recommendation."
    ),
)
async def analyze(
    payload: AnalyzeTickerRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> APIResponse[AnalyzeResponseData]:
    """
    Analyze endpoint.

    Args:
        payload: The frontend payload containing only the ticker.
        service: Injected ``AnalysisService`` instance.

    Returns:
        An ``APIResponse`` containing the analysis results.
    """
    request = AnalyzeRequest(
        ticker=payload.ticker,
        query=f"Analyze {payload.ticker}",
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

    result = service.analyze(request)

    return APIResponse.success_response(
        message=f"Analysis completed for {request.ticker}",
        data=result,
    )
