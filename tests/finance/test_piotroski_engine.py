from app.finance.piotroski_engine import PiotroskiEngine


def test_engine():

    engine = PiotroskiEngine()

    score = engine.calculate(
        roa_positive=True,
        operating_cash_flow_positive=True,
        roa_improved=True,
        cash_flow_exceeds_income=True,
        lower_leverage=True,
        improved_liquidity=False,
        no_new_shares=True,
        improved_margin=True,
        improved_asset_turnover=False,
    )

    assert score.score == 7

    assert score.rating == "Average"