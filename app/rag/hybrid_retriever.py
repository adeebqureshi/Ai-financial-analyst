"""
Hybrid retriever.
"""

from __future__ import annotations

from app.rag.bm25 import BM25Retriever
from app.rag.embedding import Embedding
from app.rag.retriever import Retriever
from app.rag.search_result import SearchResult


class HybridRetriever:

    def __init__(self) -> None:

        self.semantic = Retriever()

        self.keyword = BM25Retriever()

    def search(
        self,
        query_embedding: Embedding,
        documents: list[Embedding],
        k: int = 5,
    ) -> list[SearchResult]:

        semantic = self.semantic.search(
            query_embedding,
            documents,
            k=len(documents),
        )

        keyword = self.keyword.search(
            query_embedding.text,
            documents,
            k=len(documents),
        )

        scores: dict[str, float] = {}

        lookup = {
            doc.text: doc
            for doc in documents
        }

        for rank, result in enumerate(semantic):
            scores[result.embedding.text] = (
                scores.get(
                    result.embedding.text,
                    0.0,
                )
                + (len(documents) - rank)
            )

        for rank, doc in enumerate(keyword):
            scores[doc.text] = (
                scores.get(
                    doc.text,
                    0.0,
                )
                + (len(documents) - rank)
            )

        merged = [
            SearchResult(
                embedding=lookup[text],
                score=score,
            )
            for text, score in scores.items()
        ]

        merged.sort(
            key=lambda result: result.score,
            reverse=True,
        )

        return merged[:k]