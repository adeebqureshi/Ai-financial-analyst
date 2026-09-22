from app.agents.auditor import AuditorAgent
from app.agents.report import InvestmentReport
def test_auditor():
    auditor = AuditorAgent()
    report = InvestmentReport(
        company="Apple",
        title="Apple Report",
        body="""
Financial Metrics
Revenue increased.
ROE: 25%
ROA: 15%