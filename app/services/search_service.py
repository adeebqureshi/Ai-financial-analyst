from __future__ import annotations
from app.core.config import Settings
from app.core.logging import get_logger
from app.schemas.analysis import SearchRequest
from app.schemas.responses import SearchHitData, SearchResultData
from app.services.document_service import DocumentService
logger = get_logger(__name__)
class SearchService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._documents = DocumentService(settings)
    def search(self, request: SearchRequest, owner_id: str | None = None) -> SearchResultData:
        context = self._documents.retrieve(
            query=request.query,
            limit=request.limit,
            document_id=request.document_id,
            as_of_date=request.as_of_date,
            owner_id=owner_id,
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