"""
Retrieval result.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RetrievalResult:
    """
    Result returned by the Retriever Agent.
    """

    query: str

    documents: list[str]

    @property
    def count(self) -> int:
        return len(self.documents)