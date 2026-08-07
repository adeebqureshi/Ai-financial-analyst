"""
Embedding model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Embedding:
    """
    Represents a vector embedding.
    """

    text: str
    vector: list[float]

    @property
    def dimension(self) -> int:
        return len(self.vector)