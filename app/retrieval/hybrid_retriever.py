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
    ) -> list[str]:

        dense = self.dense.search(
            vector,
            limit,
        )

        dense_ids = [
            str(point.id)
            for point in dense
        ]

        sparse_ids = self.bm25.search(
            query,
            top_k=limit,
        )

        return self.fusion.fuse(
            dense_ids,
            sparse_ids,
        )