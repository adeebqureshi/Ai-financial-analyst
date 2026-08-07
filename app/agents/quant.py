"""
Quantitative analysis agent.
"""

from __future__ import annotations

from app.agents.analysis_result import AnalysisResult
from app.finance.ratio_engine import RatioEngine


class QuantAgent:
    """
    Performs quantitative financial analysis.
    """

    def __init__(self) -> None:

        self.ratio_engine = RatioEngine()

    def analyze(
        self,
        company: str,
    ) -> AnalysisResult:

        ratios = self.ratio_engine.calculate(
            current_assets=400,
            current_liabilities=200,
            total_liabilities=600,
            shareholders_equity=400,
            total_assets=1000,
            revenue=1000,
            gross_profit=500,
            operating_income=250,
            net_income=200,
        )

        metrics = {
            "current_ratio": ratios.current_ratio,
            "debt_to_equity": ratios.debt_to_equity,
            "return_on_assets": ratios.return_on_assets,
            "return_on_equity": ratios.return_on_equity,
            "gross_margin": ratios.gross_margin,
            "operating_margin": ratios.operating_margin,
            "net_margin": ratios.net_margin,
        }

        return AnalysisResult(
            company=company,
            summary="Financial analysis completed.",
            metrics=metrics,
        )