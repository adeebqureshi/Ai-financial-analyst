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


@dataclass(slots=True)
class ValuationResult:

    intrinsic_value: float

    upside: float

    recommendation: str