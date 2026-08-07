"""
Base financial statement.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FinancialStatement:
    """
    Base class for financial statements.
    """

    company: str
    fiscal_year: int