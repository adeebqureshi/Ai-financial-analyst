from __future__ import annotations

from app.agents.analysis_result import AnalysisResult
from app.financial.data import FinancialDataService
from app.financial.ratio_engine import RatioEngine


class QuantAgent:
    def __init__(self) -> None:
        self.ratio_engine = RatioEngine()
        self.financial_data = FinancialDataService()

    def analyze(
        self,
        company: str,
    ) -> AnalysisResult | None:
        ticker = company.upper()
        data = self.financial_data.load(ticker)
        statement = data.statement
        equity = statement.total_assets - statement.total_liabilities
        ratios = self.ratio_engine.calculate(
            current_assets=statement.current_assets,
            current_liabilities=statement.current_liabilities,
            total_liabilities=statement.total_liabilities,
            shareholders_equity=equity,
            total_assets=statement.total_assets,
            revenue=statement.revenue,
            gross_profit=statement.gross_profit,
            operating_income=statement.operating_income,
            net_income=statement.net_income,
        )
        if ratios is None:
            return None
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
            company=ticker,
            summary=f"Financial analysis completed for {ticker}.",
            metrics=metrics,
        )
