"""
openai_embedder.py

OpenAI embedding implementation.
"""

from __future__ import annotations

from openai import OpenAI

from app.core.config import settings
from app.embeddings.base_embedder import BaseEmbedder


class OpenAIEmbedder(BaseEmbedder):
    """
    OpenAI embedding provider.
    """

    def __init__(self) -> None:
        self.client = OpenAI(
            api_key=settings.openai_api_key,
        )

        self.model = settings.embedding_model

    def embed_text(
        self,
        text: str,
    ) -> list[float]:

        response = self.client.embeddings.create(
            model=self.model,
            input=text,
        )

        return response.data[0].embedding

    def embed_documents(
        self,
        documents: list[str],
    ) -> list[list[float]]:

        response = self.client.embeddings.create(
            model=self.model,
            input=documents,
        )

        return [
            item.embedding
            for item in response.data
        ]