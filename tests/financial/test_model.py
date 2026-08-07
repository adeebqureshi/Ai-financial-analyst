from app.financial.models import FinancialStatement


def test_financial_statement():

    statement = FinancialStatement(
        revenue=100,
        operating_income=30,
        net_income=25,
        total_assets=500,
        total_liabilities=200,
        cash=100,
        debt=50,
        shares_outstanding=10,
        free_cash_flow=20,
    )

    assert statement.revenue == 100

    assert statement.debt == 50