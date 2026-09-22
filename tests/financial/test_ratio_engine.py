from app.financial.ratio_engine import FinancialRatios, RatioEngine
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
def test_ratio_engine_zero_denominators_safe():
    engine = RatioEngine()
    ratios = engine.calculate(
        current_assets=0,
        current_liabilities=0,
        total_liabilities=0,
        shareholders_equity=0,
        total_assets=0,
        revenue=0,
        gross_profit=0,
        operating_income=0,
        net_income=0,
    )
    assert ratios.current_ratio == 0.0
    assert ratios.debt_to_equity == 0.0
    assert ratios.return_on_assets == 0.0
    assert ratios.return_on_equity == 0.0
    assert ratios.gross_margin == 0.0
    assert ratios.operating_margin == 0.0
    assert ratios.net_margin == 0.0
def test_financial_ratios_value_object():
    ratios = FinancialRatios(
        current_ratio=2.0,
        debt_to_equity=1.5,
        return_on_assets=0.12,
        return_on_equity=0.20,
        gross_margin=0.40,
        operating_margin=0.25,
        net_margin=0.18,
    )
    assert ratios.current_ratio == 2.0
    assert ratios.return_on_equity == 0.20