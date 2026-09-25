import pytest

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
    ratio = FinancialRatios.debt_to_equity(statement())
    assert round(ratio, 2) == 0.27


def test_roa():
    ratio = FinancialRatios.return_on_assets(statement())
    assert round(ratio, 2) == 0.03


def test_roe():
    ratio = FinancialRatios.return_on_equity(statement())
    assert round(ratio, 2) == 0.05


def test_operating_margin():
    ratio = FinancialRatios.operating_margin(statement())
    assert ratio == 0.2


def test_net_margin():
    ratio = FinancialRatios.net_margin(statement())
    assert ratio == 0.15


def test_debt_to_equity_zero_equity_returns_none():
    assert (
        FinancialRatios.debt_to_equity(
            FinancialStatement(
                revenue=1000,
                operating_income=100,
                net_income=50,
                total_assets=1000,
                total_liabilities=1000,
                cash=100,
                debt=500,
                shares_outstanding=100,
                free_cash_flow=50,
            )
        )
        is None
    )


def test_debt_to_equity_negative_equity_raises():
    with pytest.raises(ValueError, match="Equity must be positive"):
        FinancialRatios.debt_to_equity(
            FinancialStatement(
                revenue=1000,
                operating_income=100,
                net_income=50,
                total_assets=500,
                total_liabilities=1000,
                cash=100,
                debt=500,
                shares_outstanding=100,
                free_cash_flow=50,
            )
        )


def test_return_on_assets_zero_assets_returns_none():
    assert (
        FinancialRatios.return_on_assets(
            FinancialStatement(
                revenue=1000,
                operating_income=100,
                net_income=50,
                total_assets=0,
                total_liabilities=200,
                cash=100,
                debt=500,
                shares_outstanding=100,
                free_cash_flow=50,
            )
        )
        is None
    )


def test_return_on_assets_negative_assets_raises():
    with pytest.raises(ValueError, match="Assets must be positive"):
        FinancialRatios.return_on_assets(
            FinancialStatement(
                revenue=1000,
                operating_income=100,
                net_income=50,
                total_assets=-100,
                total_liabilities=200,
                cash=100,
                debt=500,
                shares_outstanding=100,
                free_cash_flow=50,
            )
        )


def test_return_on_equity_zero_equity_returns_none():
    assert (
        FinancialRatios.return_on_equity(
            FinancialStatement(
                revenue=1000,
                operating_income=100,
                net_income=50,
                total_assets=1000,
                total_liabilities=1000,
                cash=100,
                debt=500,
                shares_outstanding=100,
                free_cash_flow=50,
            )
        )
        is None
    )


def test_operating_margin_zero_revenue_returns_none():
    assert (
        FinancialRatios.operating_margin(
            FinancialStatement(
                revenue=0,
                operating_income=100,
                net_income=50,
                total_assets=1000,
                total_liabilities=200,
                cash=100,
                debt=500,
                shares_outstanding=100,
                free_cash_flow=50,
            )
        )
        is None
    )


def test_operating_margin_negative_revenue_raises():
    with pytest.raises(ValueError, match="Revenue must be positive"):
        FinancialRatios.operating_margin(
            FinancialStatement(
                revenue=-100,
                operating_income=100,
                net_income=50,
                total_assets=1000,
                total_liabilities=200,
                cash=100,
                debt=500,
                shares_outstanding=100,
                free_cash_flow=50,
            )
        )


def test_net_margin_zero_revenue_returns_none():
    assert (
        FinancialRatios.net_margin(
            FinancialStatement(
                revenue=0,
                operating_income=100,
                net_income=50,
                total_assets=1000,
                total_liabilities=200,
                cash=100,
                debt=500,
                shares_outstanding=100,
                free_cash_flow=50,
            )
        )
        is None
    )


def test_negative_margins_allowed():
    stmt = FinancialStatement(
        revenue=1000,
        operating_income=-50,
        net_income=-100,
        total_assets=5000,
        total_liabilities=2000,
        cash=400,
        debt=800,
        shares_outstanding=100,
        free_cash_flow=180,
    )
    assert FinancialRatios.operating_margin(stmt) == -0.05
    assert FinancialRatios.net_margin(stmt) == -0.10


def test_negative_roa_allowed():
    stmt = FinancialStatement(
        revenue=1000,
        operating_income=100,
        net_income=-200,
        total_assets=5000,
        total_liabilities=2000,
        cash=400,
        debt=800,
        shares_outstanding=100,
        free_cash_flow=180,
    )
    assert FinancialRatios.return_on_assets(stmt) == -0.04
