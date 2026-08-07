"""
Balance Sheet model.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.finance.statement import FinancialStatement


@dataclass(slots=True)
class BalanceSheet(FinancialStatement):

    total_assets: float

    total_liabilities: float

    shareholders_equity: float

    @property
    def accounting_equation_valid(self) -> bool:
        return abs(
            self.total_assets
            - (
                self.total_liabilities
                + self.shareholders_equity
            )
        ) < 1e-6