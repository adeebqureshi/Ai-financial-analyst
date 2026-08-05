"""
base_vector_store.py

Abstract vector database interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseVectorStore(ABC):

    @abstractmethod
    def upsert(
        self,
        ids: list[int | str],
        vectors: list[list[float]],
        payloads: list[dict],
    ) -> None:
        """
        Insert or update vectors.
        """

    @abstractmethod
    def search(
        self,
        vector: list[float],
        limit: int = 5,
    ):
        """
        Search similar vectors.
        """