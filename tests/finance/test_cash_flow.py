from app.finance.cash_flow import CashFlowStatement


def test_cash_flow():

    statement = CashFlowStatement(
        company="Apple",
        fiscal_year=2025,
        operating_cash_flow=100,
        investing_cash_flow=-40,
        financing_cash_flow=-20,
    )

    assert statement.net_cash_flow == 40