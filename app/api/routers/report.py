from __future__ import annotations
import asyncio
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from app.api.dependencies.services import get_report_service
from app.schemas.base import APIResponse
from app.schemas.responses import ReportData
from app.services.report_service import ReportService
from app.utils.tickers import normalize_ticker
router = APIRouter(prefix="/report", tags=["Report"])
class ReportTickerRequest(BaseModel):
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
        return normalize_ticker(v)
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
    result = await asyncio.to_thread(
        service.generate_ticker_report,
        ticker=payload.ticker,
        query=payload.query,
    )
    return APIResponse.success_response(
        message=f"Report generated for {result.ticker}",
        data=result,
    )