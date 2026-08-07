"""
Financial ratio calculations.
"""

from __future__ import annotations

from app.finance.ratios import FinancialRatios


class RatioEngine:

    def calculate(
        self,
        *,
        current_assets: float,
        current_liabilities: float,
        total_liabilities: float,
        shareholders_equity: float,
        total_assets: float,
        revenue: float,
        gross_profit: float,
        operating_income: float,
        net_income: float,
    ) -> FinancialRatios:

        current_ratio = (
            current_assets / current_liabilities
            if current_liabilities
            else 0.0
        )

        debt_to_equity = (
            total_liabilities / shareholders_equity
            if shareholders_equity
            else 0.0
        )

        return_on_assets = (
            net_income / total_assets
            if total_assets
            else 0.0
        )

        return_on_equity = (
            net_income / shareholders_equity
            if shareholders_equity
            else 0.0
        )

        gross_margin = (
            gross_profit / revenue
            if revenue
            else 0.0
        )

        operating_margin = (
            operating_income / revenue
            if revenue
            else 0.0
        )

        net_margin = (
            net_income / revenue
            if revenue
            else 0.0
        )

        return FinancialRatios(
            current_ratio=current_ratio,
            debt_to_equity=debt_to_equity,
            return_on_assets=return_on_assets,
            return_on_equity=return_on_equity,
            gross_margin=gross_margin,
            operating_margin=operating_margin,
            net_margin=net_margin,
        )