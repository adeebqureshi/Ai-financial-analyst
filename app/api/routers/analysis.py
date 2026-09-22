from __future__ import annotations
import asyncio
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from app.api.dependencies import rate_limit_analyze
from app.api.dependencies.services import get_analysis_service
from app.schemas.base import APIResponse
from app.schemas.responses import AnalyzeResponseData
from app.services.analysis_service import AnalysisService
from app.utils.tickers import normalize_ticker
router = APIRouter(prefix="/analyze", tags=["Analysis"])
class AnalyzeTickerRequest(BaseModel):
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
        return normalize_ticker(v)
@router.post(
    "",
    response_model=APIResponse[AnalyzeResponseData],
    summary="Analyze a company",
    description=(
        "Performs a comprehensive AI-driven financial analysis of a company "
        "using real company-specific financial statements, market data, "
        "valuation, financial health, and an investment recommendation."
    ),
    dependencies=[Depends(rate_limit_analyze)],
)
async def analyze(
    payload: AnalyzeTickerRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> APIResponse[AnalyzeResponseData]:
    result = await asyncio.to_thread(
        service.analyze_ticker,
        ticker=payload.ticker,
        query=payload.query,
    )
    return APIResponse.success_response(
        message=f"Analysis completed for {result.ticker}",
        data=result,
    )