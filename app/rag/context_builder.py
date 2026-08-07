"""
Context builder.
"""

from __future__ import annotations

from app.rag.context import Context
from app.rag.search_result import SearchResult


class ContextBuilder:

    def __init__(
        self,
        max_chunks: int = 5,
    ) -> None:

        self.max_chunks = max_chunks

    def build(
        self,
        results: list[SearchResult],
    ) -> Context:

        seen: set[str] = set()

        texts: list[str] = []

        for result in results:

            text = result.embedding.text.strip()

            if text in seen:
                continue

            seen.add(text)

            texts.append(text)

            if len(texts) >= self.max_chunks:
                break

        return Context(
            text="\n\n".join(texts),
            chunk_count=len(texts),
        )