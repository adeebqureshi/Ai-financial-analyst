"""
Financial table model.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class FinancialTable:
    """
    Represents a structured financial table.
    """

    title: str
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def column_count(self) -> int:
        if not self.headers:
            return 0
        return len(self.headers)