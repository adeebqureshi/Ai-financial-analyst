from __future__ import annotations

from app.recommendation.confidence import ConfidenceCalculator
from app.recommendation.explanation import ExplanationBuilder
from app.recommendation.recommendation import Recommendation
from app.recommendation.signal import Signal


class RecommendationEngine:

    def __init__(self) -> None:

        self.confidence = ConfidenceCalculator()

        self.explanation = ExplanationBuilder()

    def recommend(
        self,
        score: float,
    ) -> Recommendation:

        if score >= 80:
            signal = Signal.BUY
        elif score >= 50:
            signal = Signal.HOLD
        else:
            signal = Signal.SELL

        return Recommendation(
            signal=signal,
            confidence=self.confidence.calculate(score),
            explanation=self.explanation.build(signal),
        )