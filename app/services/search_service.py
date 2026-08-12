"""
Search Service

This module contains the business logic for performing semantic search over
the retrieval engine. It delegates to the existing ``DocumentService``
(which wraps ``RetrievalEngine``) and wraps the results in typed response
DTOs, preserving document / page citation metadata.

Design Decisions:
    - **Wraps existing retrieval engine**: Rather than reimplementing the
      retrieval logic, this service calls ``DocumentService.retrieve()``
      and transforms the ``RetrievalContext`` into a typed ``SearchResultData``.
    - **Document scoping**: An optional ``document_id`` restricts the search
      to a single uploaded document.
    - **Settings injection**: Consistent with other services, the constructor
      accepts ``Settings`` for dependency injection and testability.
"""

from __future__ import annotations

from app.core.config import Settings
from app.core.logging import get_logger
from app.schemas.analysis import SearchRequest
from app.schemas.responses import SearchHitData, SearchResultData
from app.services.document_service import DocumentService

logger = get_logger(__name__)


class SearchService:
    """
    Service for performing semantic search over the retrieval engine.

    Attributes:
        _settings: Application settings instance.
        _documents: Document service providing document-scoped retrieval.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize the search service.

        Args:
            settings: The application settings instance.
        """
        self._settings = settings

        self._documents = DocumentService(settings)

    def search(self, request: SearchRequest) -> SearchResultData:
        """
        Perform a semantic search.

        Args:
            request: The validated search request.

        Returns:
            A ``SearchResultData`` with the retrieval hits.
        """
        context = self._documents.retrieve(
            query=request.query,
            limit=request.limit,
            document_id=request.document_id,
            as_of_date=request.as_of_date,
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
                document_id=chunk.document_id,
                filename=chunk.filename,
                page=chunk.page,
                chunk_id=chunk.chunk_id,
            )
            for chunk in context.chunks
        ]

        return SearchResultData(
            query=request.query,
            hits=hits,
            total=len(hits),
            retrieval_time_ms=context.retrieval_time_ms,
        )
