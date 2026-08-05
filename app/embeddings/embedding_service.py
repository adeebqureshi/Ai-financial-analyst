"""
embedding_service.py

Service for generating embeddings.
"""

from __future__ import annotations

from app.embeddings.openai_embedder import OpenAIEmbedder


class EmbeddingService:
    """
    High-level embedding service.
    """

    def __init__(self) -> None:
        self.embedder = OpenAIEmbedder()

    def embed_text(
        self,
        text: str,
    ) -> list[float]:
        """
        Embed a single text.
        """

        return self.embedder.embed_text(text)

    def embed_documents(
        self,
        documents: list[str],
    ) -> list[list[float]]:
        """
        Embed multiple documents.
        """

        return self.embedder.embed_documents(documents)