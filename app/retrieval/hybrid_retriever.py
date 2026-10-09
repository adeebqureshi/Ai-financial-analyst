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
        owner_ids: list[str | None] | None = None,
    ) -> None:
        self.bm25.build(
            ids,
            documents,
            owner_ids,
        )
    def search(
        self,
        vector: list[float],
        query: str,
        limit: int = 5,
        document_id: str | None = None,
        owner_id: str | None = None,
    ) -> list[str]:
        dense = self.dense.search(
            vector,
            limit,
            document_id,
            owner_id,
        )
        return self._fuse_points(dense, query, document_id, owner_id, limit)

    def search_with_points(
        self,
        dense_points,
        query: str,
        limit: int = 5,
        document_id: str | None = None,
        owner_id: str | None = None,
    ) -> list[str]:
        """Fuse pre-fetched dense points with BM25 (avoids a 2nd Qdrant call)."""
        return self._fuse_points(dense_points, query, document_id, owner_id, limit)

    def _fuse_points(
        self,
        dense_points,
        query: str,
        document_id: str | None,
        owner_id: str | None,
        limit: int,
    ) -> list[str]:
        dense_ids = []
        for point in dense_points:
            payload = getattr(point, "payload", None) or {}
            chunk_id = payload.get("chunk_id")
            dense_ids.append(
                chunk_id if chunk_id else str(point.id)
            )
        sparse_ids = self.bm25.search(
            query,
            top_k=limit * 3,
            owner_id=owner_id,
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
