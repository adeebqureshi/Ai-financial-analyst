"""
Income Statement model.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.finance.statement import FinancialStatement


@dataclass(slots=True)
class IncomeStatement(FinancialStatement):

    revenue: float

    operating_income: float

    net_income: float

    eps: float