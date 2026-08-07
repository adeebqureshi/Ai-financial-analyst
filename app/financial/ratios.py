"""
ratios.py

Financial ratio calculations.
"""

from __future__ import annotations

from app.financial.models import FinancialStatement


class FinancialRatios:

    @staticmethod
    def debt_to_equity(
        statement: FinancialStatement,
    ) -> float:

        equity = (
            statement.total_assets
            - statement.total_liabilities
        )

        if equity <= 0:
            raise ValueError("Equity must be positive.")

        return statement.debt / equity

    @staticmethod
    def return_on_assets(
        statement: FinancialStatement,
    ) -> float:

        if statement.total_assets <= 0:
            raise ValueError("Assets must be positive.")

        return (
            statement.net_income
            / statement.total_assets
        )

    @staticmethod
    def return_on_equity(
        statement: FinancialStatement,
    ) -> float:

        equity = (
            statement.total_assets
            - statement.total_liabilities
        )

        if equity <= 0:
            raise ValueError("Equity must be positive.")

        return (
            statement.net_income
            / equity
        )

    @staticmethod
    def operating_margin(
        statement: FinancialStatement,
    ) -> float:

        if statement.revenue <= 0:
            raise ValueError("Revenue must be positive.")

        return (
            statement.operating_income
            / statement.revenue
        )

    @staticmethod
    def net_margin(
        statement: FinancialStatement,
    ) -> float:

        if statement.revenue <= 0:
            raise ValueError("Revenue must be positive.")

        return (
            statement.net_income
            / statement.revenue
        )