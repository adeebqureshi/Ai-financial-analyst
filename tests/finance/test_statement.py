from app.finance.statement import FinancialStatement


def test_statement():

    statement = FinancialStatement(
        company="Apple",
        fiscal_year=2025,
    )

    assert statement.company == "Apple"

    assert statement.fiscal_year == 2025