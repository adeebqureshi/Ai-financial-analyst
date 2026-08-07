from app.parsing.statement import FinancialStatement


def test_statement():

    statement = FinancialStatement(
        name="Balance Sheet",
        content="Assets Liabilities Equity",
    )

    assert statement.name == "Balance Sheet"

    assert statement.word_count == 3