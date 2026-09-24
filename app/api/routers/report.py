from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from app.api.dependencies.services import get_report_service
from app.core.exceptions import FinancialAnalystError
from app.core.logging import get_logger
from app.schemas.base import APIResponse, ErrorDetail
from app.schemas.responses import ReportData
from app.services.report_service import ReportService
from app.utils.tickers import normalize_ticker

logger = get_logger(__name__)
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
):
    try:
        result = await asyncio.to_thread(
            service.generate_ticker_report,
            ticker=payload.ticker,
            query=payload.query,
        )
        
        # Moved inside the try-block so Pydantic serialization errors or AttributeErrors 
        # are safely caught and formatted as structured JSON
        return APIResponse.success_response(
            message=f"Report generated for {result.ticker}",
            data=result,
        )
        
    except FinancialAnalystError as exc:
        logger.warning("Report generation failed: %s (%s)", exc.message, exc.error_code)
        response = APIResponse.error_response(
            message=exc.message,
            errors=[ErrorDetail(message=exc.message, code=exc.error_code)],
        )
        return JSONResponse(status_code=502, content=response.model_dump(mode="json"))
        
    except Exception as exc:  # noqa: BLE001 - convert unknowns to safe payload
        logger.exception("Report generation failed for %s: %s", payload.ticker, exc)
        response = APIResponse.error_response(
            message=f"Report generation failed for {payload.ticker}: {exc}",
            errors=[ErrorDetail(message=str(exc) or exc.__class__.__name__, code="REPORT_FAILED")],
        )
        return JSONResponse(status_code=500, content=response.model_dump(mode="json"))