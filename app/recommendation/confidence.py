from __future__ import annotations


class ConfidenceCalculator:

    def calculate(
        self,
        score: float,
    ) -> float:

        score = max(0.0, min(score, 100.0))

        return score / 100.0