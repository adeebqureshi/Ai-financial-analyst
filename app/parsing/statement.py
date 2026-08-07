"""
Financial statement model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FinancialStatement:
    """
    Represents a detected financial statement section.
    """

    name: str
    content: str

    @property
    def word_count(self) -> int:
        return len(self.content.split())