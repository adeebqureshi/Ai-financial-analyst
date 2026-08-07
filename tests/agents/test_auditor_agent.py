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
""",
    )

    result = auditor.audit(
        report,
    )

    assert result.passed

    assert result.issue_count == 0


def test_short_report():

    auditor = AuditorAgent()

    report = InvestmentReport(
        company="Apple",
        title="Apple Report",
        body="Short",
    )

    result = auditor.audit(
        report,
    )

    assert not result.passed

    assert result.issue_count > 0