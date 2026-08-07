from app.recommendation.explanation import ExplanationBuilder
from app.recommendation.signal import Signal


def test_explanation():

    builder = ExplanationBuilder()

    text = builder.build(
        Signal.BUY,
    )

    assert "positive" in text.lower()