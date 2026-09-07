"""
Financial domain models.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FinancialStatement:

    revenue: float

    operating_income: float

    net_income: float

    total_assets: float

    total_liabilities: float

    cash: float

    debt: float

    shares_outstanding: float

    free_cash_flow: float

    gross_profit: float = 0.0

    # Current assets / liabilities from the balance sheet. Used to compute
    # the real current ratio instead of a fabricated proxy. Defaults to 0.0
    # so legacy callers that construct a statement without these fields
    # continue to work unchanged.
    current_assets: float = 0.0

    current_liabilities: float = 0.0


@dataclass(slots=True)
class ValuationResult:

    intrinsic_value: float

    upside: float

    recommendation: str