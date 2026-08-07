"""
Cash Flow Statement model.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.finance.statement import FinancialStatement


@dataclass(slots=True)
class CashFlowStatement(FinancialStatement):

    operating_cash_flow: float

    investing_cash_flow: float

    financing_cash_flow: float

    @property
    def net_cash_flow(self) -> float:
        return (
            self.operating_cash_flow
            + self.investing_cash_flow
            + self.financing_cash_flow
        )