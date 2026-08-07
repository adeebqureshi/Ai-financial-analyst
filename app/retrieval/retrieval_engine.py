"""
retrieval_engine.py

Production retrieval engine.
"""

from __future__ import annotations

import time

from app.embeddings.embedding_service import EmbeddingService
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.metadata_store import MetadataStore
from app.retrieval.models import RetrievalContext


class RetrievalEngine:
    """
    High-level retrieval orchestration.
    """

    def __init__(self) -> None:

        self.embedder = EmbeddingService()

        self.retriever = HybridRetriever()

        self.metadata = MetadataStore()

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

    def retrieve(
        self,
        query: str,
        limit: int = 5,
    ) -> RetrievalContext:

        start = time.perf_counter()

        vector = self.embedder.embed_text(
            query,
        )

        ids = self.retriever.search(
            vector=vector,
            query=query,
            limit=limit,
        )

        chunks = self.metadata.get_many(
            ids,
        )

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        return RetrievalContext(
            query=query,
            chunks=chunks,
            retrieval_time_ms=elapsed,
        )