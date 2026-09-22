from __future__ import annotations
import asyncio
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from app.api.dependencies.services import get_compare_service
from app.schemas.base import APIResponse
from app.schemas.responses import CompareResponseData
from app.services.compare_service import CompareService
from app.utils.tickers import normalize_ticker
router = APIRouter(prefix="/compare", tags=["Compare"])
class CompareTickersRequest(BaseModel):
    tickers: list[str] = Field(
        ...,
        min_length=2,
        max_length=10,
        description="List of 2-10 ticker symbols to compare.",
    )
    @field_validator("tickers")
    @classmethod
    def validate_ticker_list(cls, v: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for raw in v:
            ticker = normalize_ticker(raw)
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
        description=(
            "Compares multiple companies. Each company is analyzed using its "
            "own real, company-specific financial data, market data and risk "
            "scores."
        ),
    )
    async def compare(
        payload: CompareTickersRequest,
        service: CompareService = Depends(get_compare_service),
    ) -> APIResponse[CompareResponseData]:
        result = await asyncio.to_thread(service.compare_tickers, payload.tickers)
        return APIResponse.success_response(
            message=f"Comparison completed for {len(result.results)} tickers",
            data=result,
        )