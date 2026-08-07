from app.agents.report import InvestmentReport
from app.agents.workflow_result import WorkflowResult


def test_workflow():

    report = InvestmentReport(
        company="Apple",
        title="Apple Report",
        body="Financial Metrics Revenue ROE ROA Growth",
    )

    result = WorkflowResult(
        report=report,
        success=True,
    )

    assert result.success

    assert result.company == "Apple"