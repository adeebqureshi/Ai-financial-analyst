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
    ) -> FinancialRatios | None:
        try:
            if any(
                denominator == 0
                for denominator in (
                    current_liabilities,
                    shareholders_equity,
                    total_assets,
                    revenue,
                )
            ):
                return None
            return FinancialRatios(
                current_ratio=current_assets / current_liabilities,
                debt_to_equity=total_liabilities / shareholders_equity,
                return_on_assets=net_income / total_assets,
                return_on_equity=net_income / shareholders_equity,
                gross_margin=gross_profit / revenue,
                operating_margin=operating_income / revenue,
                net_margin=net_income / revenue,
            )
        except ZeroDivisionError:
            return None
