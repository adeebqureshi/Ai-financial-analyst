from __future__ import annotations
import time
from datetime import date
from app.core.logging import get_logger
from app.embeddings.embedding_service import EmbeddingService
from app.retrieval.temporal_metadata import TemporalMetadata
from app.retrieval.filters import apply_temporal_filter
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.metadata_store import MetadataStore
from app.retrieval.models import RetrievalContext, RetrievedChunk
logger = get_logger(__name__)
class RetrievalEngine:
    # How many candidates to fetch per requested result when the
    # cross-encoder reranker is active. Reranking a small pool is
    # pointless, so the pool is widened and then trimmed back to `limit`.
    _rerank_candidate_factor: int = 3

    def __init__(self) -> None:
        self.embedder = EmbeddingService()
        self.retriever = HybridRetriever()
        self.metadata = MetadataStore()
        from app.core.config import get_settings
        settings = get_settings()
        self._reranker_enabled = settings.enable_reranker
        self._reranker = None
        self._reranker_failed = False
        self._min_similarity = settings.retrieval_min_similarity
        self._last_dropped = 0
    def build(
        self,
        ids: list[str],
        documents: list[str],
    ) -> None:
        self.retriever.build(
            ids,
            documents,
        )
    def refresh(
        self,
        store,
        owner_id: str | None = None,
    ) -> None:
        points = store.get_all(owner_id=owner_id)
        ids: list[str] = []
        documents: list[str] = []
        owner_ids: list[str | None] = []
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
                owner_id=payload.get("owner_id") or None,
                valid_from=temporal.valid_from,
                valid_until=temporal.valid_until,
                transaction_time=temporal.transaction_time,
            )
            ids.append(chunk_id)
            documents.append(text)
            owner_ids.append(chunk.owner_id)
            chunks.append(chunk)
        self.retriever.build(ids, documents, owner_ids)
        self.metadata.add_many(chunks)
    def _get_reranker(self):
        if not self._reranker_enabled:
            return None
        if self._reranker is None and not self._reranker_failed:
            try:
                from app.retrieval.reranker import get_reranker
                self._reranker = get_reranker()
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
        owner_id: str | None = None,
    ) -> RetrievalContext:
        start = time.perf_counter()
        vector = self.embedder.embed_text(query)

        # A cross-encoder can only reorder what it is given, so the fusion
        # stage must over-fetch whenever reranking is enabled. Without a
        # wider pool the reranker would merely re-score the same five
        # chunks and could not improve the ordering at all.
        if self._reranker_enabled:
            candidate_limit = limit * self._rerank_candidate_factor
        else:
            candidate_limit = limit * 3 if as_of_date is not None else limit

        similarity = self.retriever.dense.similarity_scores(
            vector=vector,
            limit=candidate_limit,
            document_id=document_id,
            owner_id=owner_id,
        )

        ids = self.retriever.search(
            vector=vector,
            query=query,
            limit=candidate_limit,
            document_id=document_id,
            owner_id=owner_id,
        )
        chunks = self.metadata.get_many(ids)
        for rank, chunk in enumerate(chunks):
            chunk.score = 1.0 / (60 + rank + 1)
        if owner_id is not None:
            chunks = [
                chunk for chunk in chunks
                if getattr(chunk, "owner_id", None) == owner_id
            ]
        if as_of_date is not None:
            chunks = apply_temporal_filter(
                chunks,
                as_of_date,
            )
            chunks = chunks[:limit]
        # Apply the relevance floor to the fused candidates *before*
        # reranking. Cosine similarity is a weak relevance signal, so using
        # it to discard results would throw away exactly the chunks a
        # cross-encoder would have promoted.
        chunks = self._apply_relevance_floor(chunks, similarity)
        chunks = self._rerank(
            query,
            chunks,
        )
        # The reranker widened the candidate pool, so trim back to the
        # number the caller actually asked for.
        if self._reranker_enabled:
            chunks = chunks[:limit]
        elapsed = (time.perf_counter() - start) * 1000
        logger.debug(
            "Retrieval completed: duration_ms=%.1f chunks=%d "
            "dropped_below_floor=%d scoped_to_document=%s owner_scoped=%s temporal=%s",
            elapsed,
            len(chunks),
            self._last_dropped,
            document_id is not None,
            owner_id is not None,
            as_of_date is not None,
        )
        return RetrievalContext(
            query=query,
            chunks=chunks,
            retrieval_time_ms=elapsed,
        )

    def _apply_relevance_floor(
        self,
        chunks: list[RetrievedChunk],
        similarity: dict[str, float],
    ) -> list[RetrievedChunk]:
        floor = self._min_similarity
        if floor <= 0.0 or not chunks:
            self._last_dropped = 0
            return chunks

        kept: list[RetrievedChunk] = []
        dropped = 0
        for chunk in chunks:
            score = similarity.get(chunk.id)
            if score is None and chunk.chunk_id:
                score = similarity.get(chunk.chunk_id)
            if isinstance(score, (int, float)) and not isinstance(score, bool) and score < floor:
                dropped += 1
                continue
            kept.append(chunk)

        self._last_dropped = dropped
        if dropped:
            logger.info(
                "Relevance floor %.3f dropped %d of %d retrieved chunks as "
                "insufficient evidence.",
                floor,
                dropped,
                len(chunks),
            )
        return kept
    def _rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        if not chunks:
            return chunks
        reranker = self._get_reranker()
        if reranker is None:
            return chunks
        try:
            texts = [chunk.text for chunk in chunks]
            ranked = reranker.rerank(query, texts)
            score_by_text = {
                text: float(score)
                for text, score in ranked
            }
            for chunk in chunks:
                if chunk.text in score_by_text:
                    chunk.score = score_by_text[chunk.text]
            return sorted(
                chunks,
                key=lambda chunk: chunk.score,
                reverse=True,
            )
        except Exception as exc:
            logger.debug(
                "Reranking failed (%s); keeping fused order.",
                exc,
            )
            return chunks
