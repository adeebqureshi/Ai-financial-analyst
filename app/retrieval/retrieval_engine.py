"""
retrieval_engine.py

Production retrieval engine.

The engine keeps two short-lived indexes (BM25 + in-memory metadata) that are
rebuilt from the persistent vector store via :meth:`refresh`. This keeps the
retrieval engine stateless between requests while remaining fully
document-grounded, and allows searches to be scoped to a single uploaded
document by ``document_id``.
"""

from __future__ import annotations

import time
from datetime import date

from app.core.logging import get_logger
from app.embeddings.embedding_service import EmbeddingService
from app.rag.temporal_metadata import TemporalMetadata
from app.retrieval.filters import apply_temporal_filter
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.metadata_store import MetadataStore
from app.retrieval.models import RetrievalContext, RetrievedChunk

logger = get_logger(__name__)


class RetrievalEngine:
    """
    High-level retrieval orchestration.
    """

    def __init__(self) -> None:

        self.embedder = EmbeddingService()

        self.retriever = HybridRetriever()

        self.metadata = MetadataStore()

        from app.core.config import get_settings

        self._reranker_enabled = get_settings().enable_reranker

        self._reranker = None

        self._reranker_failed = False

    def build(
        self,
        ids: list[str],
        documents: list[str],
    ) -> None:
        """
        Build retrieval indexes.
        """

        self.retriever.build(
            ids,
            documents,
        )

    def add_chunks(
        self,
        chunks,
    ) -> None:
        """
        Register metadata.
        """

        self.metadata.add_many(
            chunks,
        )

    def refresh(
        self,
        store,
    ) -> None:
        """
        Rebuild the BM25 index and metadata store from the vector store.

        This is the persistent source of truth for every indexed chunk, so
        the engine always reflects the current document library even though
        it is recreated per request.
        """
        points = store.get_all()

        ids: list[str] = []

        documents: list[str] = []

        chunks: list[RetrievedChunk] = []

        for point in points:
            payload = point.payload or {}

            text = payload.get("text", "")

            chunk_id = payload.get("chunk_id") or str(point.id)

            temporal = TemporalMetadata.from_dict(payload)

            chunk = RetrievedChunk(
                id=chunk_id,
                chunk_id=chunk_id,
                text=text,
                score=0.0,
                document_id=payload.get("document_id"),
                filename=payload.get("filename"),
                page=payload.get("page"),
                ticker=payload.get("ticker") or "",
                filing_type=payload.get("filing_type") or "",
                filing_date=None,
                section=payload.get("section") or "",
                source=payload.get("source") or "",
                parser_used=payload.get("parser_used"),
                valid_from=temporal.valid_from,
                valid_until=temporal.valid_until,
                transaction_time=temporal.transaction_time,
            )

            ids.append(chunk_id)

            documents.append(text)

            chunks.append(chunk)

        self.retriever.build(ids, documents)

        self.metadata.add_many(chunks)

    def _get_reranker(self):
        """
        Lazily create the cross-encoder reranker.

        Reranking is opt-in (``settings.enable_reranker``). Returns ``None``
        (degrading to fused ranking) when disabled or when the model cannot
        be loaded — e.g. offline or missing download.
        """
        if not self._reranker_enabled:
            return None

        if self._reranker is None and not self._reranker_failed:
            try:
                from app.retrieval.reranker import Reranker

                self._reranker = Reranker()
            except Exception as exc:
                self._reranker_failed = True

                logger.warning(
                    "Reranker unavailable (%s); using hybrid fusion ranking.",
                    exc,
                )

        return self._reranker

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        document_id: str | None = None,
        as_of_date: date | None = None,
    ) -> RetrievalContext:
        """
        Retrieve relevant chunks, optionally scoped to a single document.

        Args:
            query: The search query.
            limit: Maximum number of chunks to return.
            document_id: Optional document to scope retrieval to.
            as_of_date: Optional historical date. When provided, only chunks
                whose bitemporal metadata proves the information was known
                and valid by ``as_of_date`` are returned. This is the
                look-ahead-bias guard: future information (transaction_time >
                as_of_date) can never reach the evidence set.
        """
        start = time.perf_counter()

        vector = self.embedder.embed_text(
            query,
        )

        # Candidate pool is intentionally wider than ``limit`` when a
        # historical date is requested so that temporal filtering does not
        # starve the final evidence set.
        candidate_limit = (
            limit * 3 if as_of_date is not None else limit
        )

        ids = self.retriever.search(
            vector=vector,
            query=query,
            limit=candidate_limit,
            document_id=document_id,
        )

        chunks = self.metadata.get_many(
            ids,
        )

        # Temporal filtering happens BEFORE reranking so future documents
        # cannot influence the reranker's scoring.
        if as_of_date is not None:
            chunks = apply_temporal_filter(
                chunks,
                as_of_date,
            )
            chunks = chunks[:limit]

        chunks = self._rerank(
            query,
            chunks,
        )

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        return RetrievalContext(
            query=query,
            chunks=chunks,
            retrieval_time_ms=elapsed,
        )

    def _rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """
        Re-rank fused chunks with the cross-encoder if available.
        """
        if not chunks:
            return chunks

        reranker = self._get_reranker()

        if reranker is None:
            return chunks

        try:
            texts = [chunk.text for chunk in chunks]

            ranked = reranker.rerank(query, texts)

            by_text = {chunk.text: chunk for chunk in chunks}

            ordered = [
                by_text[text]
                for text, _score in ranked
                if text in by_text
            ]

            for chunk, (_text, score) in zip(ordered, ranked, strict=False):
                chunk.score = float(score)

            return ordered
        except Exception as exc:
            logger.debug(
                "Reranking failed (%s); keeping fused order.",
                exc,
            )

            return chunks
