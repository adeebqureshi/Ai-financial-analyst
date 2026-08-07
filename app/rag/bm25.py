"""
Simple keyword scorer (BM25 placeholder).
"""

from __future__ import annotations

from app.rag.embedding import Embedding


class BM25Retriever:
    """
    Lightweight keyword-based retriever.
    """

    def search(
        self,
        query: str,
        documents: list[Embedding],
        k: int = 5,
    ) -> list[Embedding]:

        query_words = {
            word.lower()
            for word in query.split()
        }

        scored: list[tuple[int, Embedding]] = []

        for document in documents:

            words = {
                word.lower()
                for word in document.text.split()
            }

            score = len(query_words & words)

            scored.append(
                (
                    score,
                    document,
                )
            )

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            document
            for _, document in scored[:k]
        ]