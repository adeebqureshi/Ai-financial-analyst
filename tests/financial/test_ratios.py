from app.financial.models import FinancialStatement
from app.financial.ratios import FinancialRatios


def statement():

    return FinancialStatement(
        revenue=1000,
        operating_income=200,
        net_income=150,
        total_assets=5000,
        total_liabilities=2000,
        cash=400,
        debt=800,
        shares_outstanding=100,
        free_cash_flow=180,
    )


def test_debt_to_equity():

    ratio = FinancialRatios.debt_to_equity(
        statement()
    )

    assert round(ratio, 2) == 0.27


def test_roa():

    ratio = FinancialRatios.return_on_assets(
        statement()
    )

    assert round(ratio, 2) == 0.03


def test_roe():

    ratio = FinancialRatios.return_on_equity(
        statement()
    )

    assert round(ratio, 2) == 0.05


def test_operating_margin():

    ratio = FinancialRatios.operating_margin(
        statement()
    )

    assert ratio == 0.2


def test_net_margin():

    ratio = FinancialRatios.net_margin(
        statement()
    )

    assert ratio == 0.15