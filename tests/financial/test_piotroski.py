from app.financial.piotroski import Piotroski


def test_perfect_score():

    score = Piotroski.calculate(
        roa=0.15,
        operating_cash_flow=100,
        change_in_roa=0.03,
        accrual=10,
        change_in_leverage=-0.10,
        change_in_liquidity=0.20,
        equity_issued=False,
        change_in_gross_margin=0.05,
        change_in_asset_turnover=0.04,
    )

    assert score == 9


def test_zero_score():

    score = Piotroski.calculate(
        roa=-0.10,
        operating_cash_flow=-50,
        change_in_roa=-0.01,
        accrual=-5,
        change_in_leverage=0.10,
        change_in_liquidity=-0.20,
        equity_issued=True,
        change_in_gross_margin=-0.05,
        change_in_asset_turnover=-0.03,
    )

    assert score == 0


def test_partial_score():

    score = Piotroski.calculate(
        roa=0.10,
        operating_cash_flow=50,
        change_in_roa=-0.02,
        accrual=5,
        change_in_leverage=-0.05,
        change_in_liquidity=-0.10,
        equity_issued=False,
        change_in_gross_margin=0.03,
        change_in_asset_turnover=-0.02,
    )

    assert score == 6