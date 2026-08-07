"""
Embedding model interface.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from app.rag.embedding import Embedding


class EmbeddingModel(ABC):
    """
    Base embedding model interface.
    """

    @abstractmethod
    def embed(
        self,
        text: str,
    ) -> Embedding:
        """
        Generate an embedding for text.
        """