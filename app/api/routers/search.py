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
    result = await asyncio.to_thread(service.search, request, owner_id=_owner_id(current_user))
    return APIResponse.success_response(
        message=f"Search completed with {result.total} results",
        data=result,
    )