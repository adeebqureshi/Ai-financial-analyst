"""
RAG context model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Context:
    """
    Final context sent to the LLM.
    """

    text: str
    chunk_count: int

    @property
    def word_count(self) -> int:
        return len(self.text.split())