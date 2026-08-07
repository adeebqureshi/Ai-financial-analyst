from app.portfolio.drawdown import MaximumDrawdown


def test_drawdown():

    dd = MaximumDrawdown()

    value = dd.calculate(
        [100, 120, 90, 140]
    )

    assert value > 0