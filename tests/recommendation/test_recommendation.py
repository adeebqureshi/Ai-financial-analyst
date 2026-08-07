from app.recommendation.recommendation import Recommendation
from app.recommendation.signal import Signal


def test_recommendation():

    rec = Recommendation(
        signal=Signal.BUY,
        confidence=0.95,
        explanation="Strong fundamentals.",
    )

    assert rec.signal == Signal.BUY

    assert rec.confidence == 0.95