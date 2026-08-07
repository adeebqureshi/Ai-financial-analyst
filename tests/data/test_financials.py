from app.data.financials import FinancialStatements


def test_financials():

    statements = FinancialStatements()

    income = statements.income_statement(
        "AAPL",
    )

    assert income is not None