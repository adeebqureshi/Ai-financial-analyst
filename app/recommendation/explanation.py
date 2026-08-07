from __future__ import annotations

from app.recommendation.signal import Signal


class ExplanationBuilder:

    def build(
        self,
        signal: Signal,
    ) -> str:

        if signal == Signal.BUY:
            return "Financial indicators suggest a positive outlook."

        if signal == Signal.SELL:
            return "Financial indicators suggest elevated risk."

        return "Financial indicators are mixed."