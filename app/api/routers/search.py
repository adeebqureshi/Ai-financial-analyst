"""
Search Router

This module defines the semantic search endpoint (``POST /search``).

Design Decisions:
    - **No business logic in route**: The route handler delegates entirely
      to ``SearchService.search()``.
    - **Dependency injection**: ``SearchService`` is injected via
      ``Depends(get_search_service)``, making it overridable in tests.
    - **Ownership isolation**: Search results are scoped to the authenticated
      user's documents (or anonymous bucket when auth is disabled).
    - **Standard response format**: Returns ``APIResponse[SearchResultData]``.
    - **Rate limiting**: Endpoint is rate limited per user/IP.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends

from app.api.dependencies import rate_limit_search
from app.api.dependencies.services import get_search_service
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.schemas.analysis import SearchRequest
from app.schemas.base import APIResponse
from app.schemas.responses import SearchResultData
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


def _owner_id(current_user: User | None) -> str | None:
    """Return the owner id for the caller (None when auth is disabled)."""
    return current_user.id if current_user is not None else None


@router.post(
    "",
    response_model=APIResponse[SearchResultData],
    summary="Semantic search",
    description=(
        "Performs a semantic search over the retrieval engine and returns "
        "relevant document chunks with scores and metadata. Results are scoped "
        "to the authenticated user's documents."
    ),
    dependencies=[Depends(rate_limit_search)],
)
async def search(
    request: SearchRequest,
    service: SearchService = Depends(get_search_service),
    current_user: User | None = Depends(get_current_user),
) -> APIResponse[SearchResultData]:
    """
    Semantic search endpoint.

    Args:
        request: The validated search request.
        service: Injected ``SearchService`` instance.
        current_user: The authenticated owner (``None`` when auth disabled).

    Returns:
        An ``APIResponse`` containing the search results.
    """
    result = await asyncio.to_thread(service.search, request, owner_id=_owner_id(current_user))

    return APIResponse.success_response(
        message=f"Search completed with {result.total} results",
        data=result,
    )