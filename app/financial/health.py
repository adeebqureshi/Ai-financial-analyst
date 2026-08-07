"""
health.py

Overall financial health assessment.
"""

from __future__ import annotations

from app.financial.altman import AltmanZScore
from app.financial.beneish import BeneishMScore


class FinancialHealth:

    @staticmethod
    def score(
        piotroski: int,
        altman: float,
        beneish: float,
    ) -> int:

        score = 0

        if piotroski >= 8:
            score += 40
        elif piotroski >= 6:
            score += 30
        elif piotroski >= 4:
            score += 20
        else:
            score += 10

        if AltmanZScore.interpretation(altman) == "SAFE":
            score += 35
        elif AltmanZScore.interpretation(altman) == "GREY":
            score += 20
        else:
            score += 5

        if BeneishMScore.interpretation(beneish) == "LOW_RISK":
            score += 25
        else:
            score += 5

        return score

    @staticmethod
    def rating(
        score: int,
    ) -> str:

        if score >= 85:
            return "EXCELLENT"

        if score >= 70:
            return "GOOD"

        if score >= 50:
            return "FAIR"

        return "POOR"