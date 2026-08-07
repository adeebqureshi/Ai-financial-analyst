from app.recommendation.engine import RecommendationEngine
from app.recommendation.signal import Signal


def test_engine():

    engine = RecommendationEngine()

    result = engine.recommend(
        90,
    )

    assert result.signal == Signal.BUY

    assert result.confidence == 0.9