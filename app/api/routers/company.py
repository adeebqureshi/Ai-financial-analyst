from __future__ import annotations
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Path
from app.api.dependencies.services import get_company_service
from app.schemas.base import APIResponse
from app.schemas.responses import CompanyData
from app.services.company_service import CompanyService
from app.utils.tickers import normalize_ticker
router = APIRouter(prefix="/company", tags=["Company"])
@router.get(
    "/{ticker}",
    response_model=APIResponse[CompanyData],
    summary="Get company profile",
    description="Returns the company profile for a given ticker symbol.",
)
async def get_company(
    ticker: str = Path(..., min_length=1, max_length=5, description="Ticker symbol (1-5 letters)."),
    service: CompanyService = Depends(get_company_service),
) -> APIResponse[CompanyData]:
    try:
        symbol = normalize_ticker(ticker)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid ticker symbol.")
    result = await asyncio.to_thread(service.get_company, symbol)
    if result.name == symbol and result.sector is None and result.industry is None:
        raise HTTPException(status_code=404, detail=f"Company '{symbol}' was not found.")
    return APIResponse.success_response(
        message=f"Company profile retrieved for {symbol}",
        data=result,
    )