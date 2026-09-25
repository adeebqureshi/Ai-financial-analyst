from __future__ import annotations

from app.financial.models import FinancialStatement


class FinancialRatios:
    @staticmethod
    def debt_to_equity(
        statement: FinancialStatement,
    ) -> float | None:
        equity = statement.total_assets - statement.total_liabilities

        if equity == 0:
            return None
        if equity < 0:
            raise ValueError("Equity must be positive.")

        try:
            return statement.debt / equity
        except ZeroDivisionError:
            return None

    @staticmethod
    def return_on_assets(
        statement: FinancialStatement,
    ) -> float | None:
        if statement.total_assets == 0:
            return None
        if statement.total_assets < 0:
            raise ValueError("Assets must be positive.")

        try:
            return statement.net_income / statement.total_assets
        except ZeroDivisionError:
            return None

    @staticmethod
    def return_on_equity(
        statement: FinancialStatement,
    ) -> float | None:
        equity = statement.total_assets - statement.total_liabilities

        if equity == 0:
            return None
        if equity < 0:
            raise ValueError("Equity must be positive.")

        try:
            return statement.net_income / equity
        except ZeroDivisionError:
            return None

    @staticmethod
    def operating_margin(
        statement: FinancialStatement,
    ) -> float | None:
        if statement.revenue == 0:
            return None
        if statement.revenue < 0:
            raise ValueError("Revenue must be positive.")

        try:
            return statement.operating_income / statement.revenue
        except ZeroDivisionError:
            return None

    @staticmethod
    def net_margin(
        statement: FinancialStatement,
    ) -> float | None:
        if statement.revenue == 0:
            return None
        if statement.revenue < 0:
            raise ValueError("Revenue must be positive.")

        try:
            return statement.net_income / statement.revenue
        except ZeroDivisionError:
            return None
