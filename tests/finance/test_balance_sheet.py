from app.finance.balance_sheet import BalanceSheet


def test_balance_sheet():

    sheet = BalanceSheet(
        company="Apple",
        fiscal_year=2025,
        total_assets=100,
        total_liabilities=60,
        shareholders_equity=40,
    )

    assert sheet.accounting_equation_valid