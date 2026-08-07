"""
analysis.py

Unified financial analysis engine.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.financial.health import FinancialHealth
from app.financial.models import FinancialStatement
from app.financial.piotroski import Piotroski
from app.financial.altman import AltmanZScore
from app.financial.beneish import BeneishMScore
from app.financial.valuation import ValuationEngine


@dataclass(slots=True)
class AnalysisResult:

    intrinsic_value: float
    upside: float
    recommendation: str

    piotroski_score: int

    altman_score: float

    beneish_score: float

    health_score: int

    health_rating: str


class FinancialAnalysisEngine:

    def __init__(self):

        self.valuation = ValuationEngine()

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
    ) -> AnalysisResult:

        valuation = self.valuation.evaluate(
            statement=statement,
            current_price=current_price,
            growth_rate=growth_rate,
            risk_free_rate=risk_free_rate,
            beta=beta,
            market_return=market_return,
            tax_rate=tax_rate,
        )

        health = FinancialHealth.score(
            piotroski_score,
            altman_score,
            beneish_score,
        )

        return AnalysisResult(
            intrinsic_value=valuation.intrinsic_value,
            upside=valuation.upside,
            recommendation=valuation.recommendation,
            piotroski_score=piotroski_score,
            altman_score=altman_score,
            beneish_score=beneish_score,
            health_score=health,
            health_rating=FinancialHealth.rating(
                health
            ),
        )