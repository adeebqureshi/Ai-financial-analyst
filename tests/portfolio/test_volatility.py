from app.portfolio.volatility import Volatility


def test_volatility():

    vol = Volatility()

    assert vol.calculate(
        [0.1, 0.2, 0.15]
    ) > 0