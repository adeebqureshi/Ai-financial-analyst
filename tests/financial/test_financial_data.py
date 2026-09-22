import pandas as pd
import pytest
from app.core.exceptions import RetrievalError
from app.financial.data import FinancialDataService
_MILLION = 1_000_000.0
INCOME = pd.DataFrame(
    {
        "2024": [1000.0, 250.0, 200.0, 500.0, 100.0, 400.0],
        "2023": [900.0, 200.0, 150.0, 450.0, 100.0, 360.0],
    },
    index=[
        "Total Revenue",
        "Operating Income",
        "Net Income",
        "Gross Profit",
        "Diluted Average Shares",
        "Cost Of Revenue",
    ],
)
BALANCE = pd.DataFrame(
    {
        "2024": [5000.0, 2000.0, 1500.0, 500.0, 700.0, 400.0, 300.0, 1200.0],
        "2023": [4500.0, 1800.0, 1300.0, 400.0, 600.0, 300.0, 250.0, 1000.0],
    },
    index=[
        "Total Assets",
        "Total Liabilities Net Minority Interest",
        "Current Assets",
        "Current Liabilities",
        "Total Debt",
        "Cash And Cash Equivalents",
        "Net PPE",
        "Retained Earnings",
    ],
)
CASHFLOW = pd.DataFrame(
    {
        "2024": [600.0, 700.0],
        "2023": [500.0, 580.0],
    },
    index=["Free Cash Flow", "Operating Cash Flow"],
)
def test_build_statement_populates_current_assets_and_liabilities():
    service = FinancialDataService()
    stmt = service._build_statement("TEST", INCOME, BALANCE, CASHFLOW, {})
    assert stmt.total_assets == 5000.0 / _MILLION
    assert stmt.total_liabilities == 2000.0 / _MILLION
    assert stmt.current_assets == 1500.0 / _MILLION
    assert stmt.current_liabilities == 500.0 / _MILLION
    assert stmt.free_cash_flow == 600.0 / _MILLION
    assert stmt.shares_outstanding == 100.0 / _MILLION
    ratio = stmt.current_assets / stmt.current_liabilities
    assert ratio == pytest.approx(3.0, abs=1e-6)
def test_build_statement_raises_when_free_cash_flow_undeterminable():
    service = FinancialDataService()
    bad_cashflow = pd.DataFrame(
        {"2024": [None], "2023": [None]},
        index=["Depreciation"],
    )
    with pytest.raises(RetrievalError):
        service._build_statement("TEST", INCOME, BALANCE, bad_cashflow, {})