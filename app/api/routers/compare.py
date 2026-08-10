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
from app.schemas.base import APIResponse
from app.schemas.responses import CompareResponseData
from app.services.compare_service import CompareService

router = APIRouter(prefix="/compare", tags=["Compare"])


class CompareTickersRequest(BaseModel):
    """
    Frontend payload for ``POST /compare``.

    The frontend only supplies tickers; each company is analyzed server-side
    using its own real financial data.
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
        """
        Compare endpoint.

        Args:
            payload: The frontend payload containing only the tickers.
            service: Injected ``CompareService`` instance.

        Returns:
            An ``APIResponse`` containing the comparison results.
        """
        result = service.compare_tickers(payload.tickers)

        return APIResponse.success_response(
            message=f"Comparison completed for {len(result.results)} tickers",
            data=result,
        )
