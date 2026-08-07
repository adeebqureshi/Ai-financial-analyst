from app.financial.dcf import DCFValuation


def test_intrinsic_value():

    value = DCFValuation.intrinsic_value(
        free_cash_flow=1000,
        growth_rate=0.10,
        discount_rate=0.12,
        terminal_growth=0.03,
        years=5,
        shares_outstanding=100,
    )

    assert value > 0


def test_invalid_discount_rate():

    try:

        DCFValuation.intrinsic_value(
            free_cash_flow=1000,
            growth_rate=0.10,
            discount_rate=0.03,
            terminal_growth=0.03,
            years=5,
            shares_outstanding=100,
        )

    except ValueError:

        assert True

    else:

        assert False


def test_invalid_shares():

    try:

        DCFValuation.intrinsic_value(
            free_cash_flow=1000,
            growth_rate=0.10,
            discount_rate=0.12,
            terminal_growth=0.03,
            years=5,
            shares_outstanding=0,
        )

    except ValueError:

        assert True

    else:

        assert False