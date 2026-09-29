from __future__ import annotations
from app.agents.financial_analyst import FinancialAnalystAgent
from app.financial.models import FinancialStatement
from app.ingestion.services.market_service import MarketService
from app.ingestion.services.sec_service import SECService
class FinancialPipeline:
    def __init__(self) -> None:
        self.analyst = FinancialAnalystAgent()
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
        company = self.sec.get_company(ticker)
        market = self.market.get_market_data(ticker)
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
        return {
            "company": company,
            "market": market,
            "analysis": analysis,
        }
