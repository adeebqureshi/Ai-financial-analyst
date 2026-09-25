from app.financial.models import FinancialStatement
from app.financial.valuation import ValuationEngine


def _base_statement(**overrides) -> FinancialStatement:
    values = dict(
        revenue=1000,
        operating_income=250,
        net_income=200,
        total_assets=5000,
        total_liabilities=1500,
        cash=500,
        debt=700,
        shares_outstanding=100,
        free_cash_flow=250,
    )
    values.update(overrides)
    return FinancialStatement(**values)


def test_valuation_engine():
    statement = _base_statement()
    engine = ValuationEngine()
    result = engine.evaluate(
        statement=statement,
        current_price=15,
        growth_rate=0.08,
        risk_free_rate=0.04,
        beta=1.1,
        market_return=0.10,
        tax_rate=0.25,
    )
    assert result.intrinsic_value > 0
    assert isinstance(result.recommendation, str)


def test_valuation_subtracts_net_debt():
    engine = ValuationEngine()
    params = dict(
        current_price=15,
        growth_rate=0.08,
        risk_free_rate=0.04,
        beta=1.1,
        market_return=0.10,
        tax_rate=0.25,
    )
    no_cash = engine.evaluate(statement=_base_statement(cash=0.0), **params)
    with_cash = engine.evaluate(statement=_base_statement(cash=500.0), **params)
    expected_increase = 500.0 / 100.0
    assert abs((with_cash.intrinsic_value - no_cash.intrinsic_value) - expected_increase) < 1e-6
