from app.finance.ratio_engine import RatioEngine


def test_ratio_engine():

    engine = RatioEngine()

    ratios = engine.calculate(
        current_assets=400,
        current_liabilities=200,
        total_liabilities=600,
        shareholders_equity=400,
        total_assets=1000,
        revenue=1000,
        gross_profit=500,
        operating_income=250,
        net_income=200,
    )

    assert ratios.current_ratio == 2.0

    assert ratios.debt_to_equity == 1.5

    assert ratios.return_on_assets == 0.2

    assert ratios.return_on_equity == 0.5

    assert ratios.gross_margin == 0.5

    assert ratios.operating_margin == 0.25

    assert ratios.net_margin == 0.2