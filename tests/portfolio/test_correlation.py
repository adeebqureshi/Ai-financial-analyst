from app.portfolio.correlation import Correlation


def test_correlation():

    corr = Correlation()

    value = corr.calculate(
        [1, 2, 3],
        [2, 4, 6],
    )

    assert value > 0.99