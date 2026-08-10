"""
Unified financial document model.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.ingestion.metadata import DocumentMetadata


@dataclass(slots=True)
class FinancialDocument:
    """
    Canonical document returned by every loader.
    """

    text: str
    metadata: DocumentMetadata
    tables: list[str] = field(default_factory=list)
    sections: list[str] = field(default_factory=list)
    pages: list[str] = field(default_factory=list)

    @property
    def word_count(self) -> int:
        return len(self.text.split())

    @property
    def is_empty(self) -> bool:
        return self.word_count == 0