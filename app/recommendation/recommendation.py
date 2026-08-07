from __future__ import annotations

from dataclasses import dataclass

from app.recommendation.signal import Signal


@dataclass(slots=True)
class Recommendation:

    signal: Signal

    confidence: float

    explanation: str