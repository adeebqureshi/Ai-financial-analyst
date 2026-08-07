"""
Report Writer Agent.
"""

from __future__ import annotations

from app.agents.analysis_result import AnalysisResult
from app.agents.report import InvestmentReport
from app.agents.retrieval_result import RetrievalResult


class ReportWriterAgent:
    """
    Generates investment reports.
    """

    def write(
        self,
        retrieval: RetrievalResult,
        analysis: AnalysisResult,
    ) -> InvestmentReport:

        body = (
            f"Query: {retrieval.query}\n\n"
            f"Documents Retrieved: {retrieval.count}\n\n"
            f"{analysis.summary}\n\n"
            "Financial Metrics:\n"
        )

        for name, value in analysis.metrics.items():
            body += f"- {name}: {value}\n"

        return InvestmentReport(
            company=analysis.company,
            title=f"{analysis.company} Investment Report",
            body=body,
        )