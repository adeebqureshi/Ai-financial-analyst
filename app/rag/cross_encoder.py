"""
Cross encoder interface.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod


class CrossEncoder(ABC):
    """
    Base interface for reranking models.
    """

    @abstractmethod
    def score(
        self,
        query: str,
        document: str,
    ) -> float:
        """
        Return a relevance score between query and document.
        """
        raise NotImplementedError