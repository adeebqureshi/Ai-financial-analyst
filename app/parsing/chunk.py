"""
Semantic chunk model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Chunk:
    """
    Represents one semantic chunk.
    """

    id: int
    text: str
    section: str

    @property
    def word_count(self) -> int:
        return len(self.text.split())