"""
base_embedder.py

Abstract interface for embedding models.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseEmbedder(ABC):
    """
    Base class for all embedding providers.
    """

    @abstractmethod
    def embed_text(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate embedding for a single text.
        """

    @abstractmethod
    def embed_documents(
        self,
        documents: list[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple documents.
        """