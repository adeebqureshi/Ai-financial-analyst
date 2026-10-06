from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.data.company_search import normalize_query, search_companies
from app.schemas.base import APIResponse

router = APIRouter(prefix="/companies", tags=["Companies"])


class CompanySuggestion(BaseModel):
    ticker: str = Field(..., description="Canonical uppercase ticker.")
    name: str = Field(..., description="Canonical company name.")
    exchange: str | None = Field(default=None, description="Listing exchange, when known.")


class CompanySearchData(BaseModel):
    query: str = Field(..., description="Echo of the normalized query.")
    results: list[CompanySuggestion] = Field(default_factory=list)


@router.get(
    "/search",
    response_model=APIResponse[CompanySearchData],
    summary="Search companies by name or ticker",
    description=(
        "Prefix/substring lookup over the curated company directory. "
        "Used by the global CompanySearch autocomplete; local filtering "
        "in the UI means this is a fallback, not a per-keystroke call."
    ),
)
def search_companies_endpoint(
    q: str = Query(default="", max_length=100, description="Company name or ticker prefix."),
    limit: int = Query(default=8, ge=1, le=20, description="Max suggestions to return."),
) -> APIResponse[CompanySearchData]:
    query = normalize_query(q)
    matches = search_companies(query, limit=limit) if query else []
    return APIResponse.success_response(
        message=f"Found {len(matches)} companies" if matches else "No companies found",
        data=CompanySearchData(
            query=query,
            results=[
                CompanySuggestion(ticker=m.ticker, name=m.name, exchange=m.exchange)
                for m in matches
            ],
        ),
    )
