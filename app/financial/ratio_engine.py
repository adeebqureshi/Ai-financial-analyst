from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FinancialRatios:
    current_ratio: float
    debt_to_equity: float
    return_on_assets: float
    return_on_equity: float
    gross_margin: float
    operating_margin: float
    net_margin: float


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
        try:
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

        except ZeroDivisionError:
            return FinancialRatios(
                current_ratio=0.0,
                debt_to_equity=0.0,
                return_on_assets=0.0,
                return_on_equity=0.0,
                gross_margin=0.0,
                operating_margin=0.0,
                net_margin=0.0,
            )