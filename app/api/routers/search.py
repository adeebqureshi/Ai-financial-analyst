"""
Search Router

This module defines the semantic search endpoint (``POST /search``).

Design Decisions:
    - **No business logic in route**: The route handler delegates entirely
      to ``SearchService.search()``.
    - **Dependency injection**: ``SearchService`` is injected via
      ``Depends(get_search_service)``, making it overridable in tests.
    - **Standard response format**: Returns ``APIResponse[SearchResultData]``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies.services import get_search_service
from app.schemas.analysis import SearchRequest
from app.schemas.base import APIResponse
from app.schemas.responses import SearchResultData
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.post(
    "",
    response_model=APIResponse[SearchResultData],
    summary="Semantic search",
    description=(
        "Performs a semantic search over the retrieval engine and returns "
        "relevant document chunks with scores and metadata."
    ),
)
async def search(
    request: SearchRequest,
    service: SearchService = Depends(get_search_service),
) -> APIResponse[SearchResultData]:
    """
    Semantic search endpoint.

    Args:
        request: The validated search request.
        service: Injected ``SearchService`` instance.

    Returns:
        An ``APIResponse`` containing the search results.
    """
    result = service.search(request)

    return APIResponse.success_response(
        message=f"Search completed with {result.total} results",
        data=result,
    )