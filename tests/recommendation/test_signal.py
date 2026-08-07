from app.recommendation.signal import Signal


def test_signal():

    assert Signal.BUY.value == "BUY"

    assert Signal.SELL.value == "SELL"