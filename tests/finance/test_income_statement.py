from app.finance.income_statement import IncomeStatement


def test_income_statement():

    statement = IncomeStatement(
        company="Apple",
        fiscal_year=2025,
        revenue=1000,
        operating_income=300,
        net_income=250,
        eps=4.25,
    )

    assert statement.revenue == 1000

    assert statement.eps == 4.25