"""
pipeline.py

End-to-end orchestration pipeline.
"""

from __future__ import annotations

from app.agents.auditor import AuditorAgent
from app.agents.financial_analyst import FinancialAnalystAgent
from app.agents.planner import PlannerAgent
from app.agents.retriever import RetrieverAgent
from app.financial.models import FinancialStatement
from app.ingestion.services.market_service import MarketService
from app.ingestion.services.sec_service import SECService


class FinancialPipeline:

    def __init__(self) -> None:

        self.planner = PlannerAgent()
        self.retriever = RetrieverAgent()
        self.analyst = FinancialAnalystAgent()
        self.auditor = AuditorAgent()

        self.sec = SECService()
        self.market = MarketService()

    def analyze_company(
        self,
        ticker: str,
        statement: FinancialStatement,
        query: str,
        growth_rate: float,
        risk_free_rate: float,
        beta: float,
        market_return: float,
        tax_rate: float,
        piotroski_score: int,
        altman_score: float,
        beneish_score: float,
    ):

        tasks = self.planner.plan(query)

        company = self.sec.get_company(ticker)

        market = self.market.get_market_data(ticker)

        context = self.retriever.retrieve(query)

        analysis = self.analyst.analyze(
            statement=statement,
            current_price=market.current_price,
            growth_rate=growth_rate,
            risk_free_rate=risk_free_rate,
            beta=beta,
            market_return=market_return,
            tax_rate=tax_rate,
            piotroski_score=piotroski_score,
            altman_score=altman_score,
            beneish_score=beneish_score,
        )

        audited = self.auditor.audit(
            analysis,
        )

        return {
            "company": company,
            "market": market,
            "tasks": tasks,
            "context": context,
            "analysis": analysis,
            "audited": audited,
        }