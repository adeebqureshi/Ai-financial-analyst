"""
Document section model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Section:
    title: str
    content: str

    @property
    def word_count(self) -> int:
        return len(self.content.split())