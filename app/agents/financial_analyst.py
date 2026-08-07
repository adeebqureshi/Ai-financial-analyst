"""
financial_analyst.py

Financial Analyst Agent.
"""

from __future__ import annotations

from app.financial.analysis import FinancialAnalysisEngine
from app.financial.models import FinancialStatement


class FinancialAnalystAgent:

    def __init__(self) -> None:

        self.engine = FinancialAnalysisEngine()

    def analyze(
        self,
        statement: FinancialStatement,
        current_price: float,
        growth_rate: float,
        risk_free_rate: float,
        beta: float,
        market_return: float,
        tax_rate: float,
        piotroski_score: int,
        altman_score: float,
        beneish_score: float,
    ):

        return self.engine.analyze(
            statement=statement,
            current_price=current_price,
            growth_rate=growth_rate,
            risk_free_rate=risk_free_rate,
            beta=beta,
            market_return=market_return,
            tax_rate=tax_rate,
            piotroski_score=piotroski_score,
            altman_score=altman_score,
            beneish_score=beneish_score,
        )