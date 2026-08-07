"""
financial_analyst.py

Main orchestration pipeline.
"""

from __future__ import annotations

from app.agents.auditor import AuditorAgent
from app.agents.financial_analyst import FinancialAnalystAgent
from app.agents.planner import PlannerAgent
from app.agents.retriever import RetrieverAgent


class FinancialAnalyst:

    def __init__(self) -> None:

        self.planner = PlannerAgent()

        self.retriever = RetrieverAgent()

        self.analyst = FinancialAnalystAgent()

        self.auditor = AuditorAgent()

    def plan(
        self,
        query: str,
    ):

        return self.planner.plan(query)

    def retrieve(
        self,
        query: str,
    ):

        return self.retriever.retrieve(query)

    def analyze(
        self,
        **kwargs,
    ):

        return self.analyst.analyze(**kwargs)

    def audit(
        self,
        analysis,
    ):

        return self.auditor.audit(analysis)