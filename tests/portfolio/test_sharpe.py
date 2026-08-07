from app.portfolio.sharpe import SharpeRatio


def test_sharpe():

    ratio = SharpeRatio()

    value = ratio.calculate(
        [0.10, 0.15, 0.08, 0.12]
    )

    assert isinstance(value, float)