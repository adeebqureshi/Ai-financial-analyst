"""
hybrid_retriever.py
"""

from __future__ import annotations

from app.retrieval.bm25_index import BM25Index
from app.retrieval.dense_retriever import DenseRetriever
from app.retrieval.rank_fusion import RankFusion


class HybridRetriever:

    def __init__(self) -> None:
        self.dense = DenseRetriever()
        self.bm25 = BM25Index()
        self.fusion = RankFusion()

    def build(
        self,
        ids: list[str],
        documents: list[str],
    ) -> None:
        self.bm25.build(
            ids,
            documents,
        )

    def search(
        self,
        vector: list[float],
        query: str,
        limit: int = 5,
        document_id: str | None = None,
    ) -> list[str]:

        dense = self.dense.search(
            vector,
            limit,
            document_id,
        )

        dense_ids = []

        for point in dense:
            payload = getattr(point, "payload", None) or {}

            chunk_id = payload.get("chunk_id")

            dense_ids.append(
                chunk_id if chunk_id else str(point.id)
            )

        sparse_ids = self.bm25.search(
            query,
            top_k=limit * 3,
        )

        if document_id:
            prefix = f"{document_id}:"

            sparse_ids = [
                doc_id
                for doc_id in sparse_ids
                if doc_id.startswith(prefix)
            ]

        return self.fusion.fuse(
            dense_ids,
            sparse_ids,
        )[:limit]