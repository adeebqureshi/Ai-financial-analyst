"""
Simple embedding retriever.
"""

from __future__ import annotations

from app.rag.embedding import Embedding
from app.rag.search_result import SearchResult
from app.rag.similarity import CosineSimilarity


class Retriever:

    def search(
        self,
        query: Embedding,
        embeddings: list[Embedding],
        k: int = 5,
    ) -> list[SearchResult]:

        results: list[SearchResult] = []

        for embedding in embeddings:

            score = CosineSimilarity.compute(
                query.vector,
                embedding.vector,
            )

            results.append(
                SearchResult(
                    embedding=embedding,
                    score=score,
                )
            )

        results.sort(
            key=lambda result: result.score,
            reverse=True,
        )

        return results[:k]