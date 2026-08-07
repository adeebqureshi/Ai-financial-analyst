"""
Search Service

This module contains the business logic for performing semantic search over
the retrieval engine. It delegates to the existing ``RetrievalEngine`` and
wraps the results in typed response DTOs.

Design Decisions:
    - **Wraps existing retrieval engine**: Rather than reimplementing the
      retrieval logic, this service calls ``RetrievalEngine.retrieve()``
      and transforms the ``RetrievalContext`` into a typed ``SearchResultData``.
    - **Settings injection**: Consistent with other services, the constructor
      accepts ``Settings`` for dependency injection and testability.
"""

from __future__ import annotations

from app.core.config import Settings
from app.core.logging import get_logger
from app.retrieval.retrieval_engine import RetrievalEngine
from app.schemas.analysis import SearchRequest
from app.schemas.responses import SearchHitData, SearchResultData

logger = get_logger(__name__)


class SearchService:
    """
    Service for performing semantic search over the retrieval engine.

    Attributes:
        _settings: Application settings instance.
        _engine: Retrieval engine instance.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize the search service.

        Args:
            settings: The application settings instance.
        """
        self._settings = settings
        self._engine = RetrievalEngine()

    def search(self, request: SearchRequest) -> SearchResultData:
        """
        Perform a semantic search.

        Args:
            request: The validated search request.

        Returns:
            A ``SearchResultData`` with the retrieval hits.
        """
        context = self._engine.retrieve(
            query=request.query,
            limit=request.limit,
        )

        hits = [
            SearchHitData(
                id=chunk.id,
                text=chunk.text,
                score=chunk.score,
                ticker=chunk.ticker,
                filing_type=chunk.filing_type,
                filing_date=chunk.filing_date,
                section=chunk.section,
                source=chunk.source,
            )
            for chunk in context.chunks
        ]

        return SearchResultData(
            query=request.query,
            hits=hits,
            total=len(hits),
            retrieval_time_ms=context.retrieval_time_ms,
        )