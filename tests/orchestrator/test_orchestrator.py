from unittest.mock import MagicMock
from unittest.mock import patch

from app.orchestrator.financial_analyst import FinancialAnalyst


@patch("app.orchestrator.financial_analyst.AuditorAgent")
@patch("app.orchestrator.financial_analyst.FinancialAnalystAgent")
@patch("app.orchestrator.financial_analyst.RetrieverAgent")
@patch("app.orchestrator.financial_analyst.PlannerAgent")
def test_workflow(
    mock_planner,
    mock_retriever,
    mock_analyst,
    mock_auditor,
):

    planner = MagicMock()
    planner.plan.return_value = ["task"]
    mock_planner.return_value = planner

    retriever = MagicMock()
    retriever.retrieve.return_value = "context"
    mock_retriever.return_value = retriever

    analyst = MagicMock()
    analyst.analyze.return_value = "analysis"
    mock_analyst.return_value = analyst

    auditor = MagicMock()
    auditor.audit.return_value = True
    mock_auditor.return_value = auditor

    app = FinancialAnalyst()

    assert app.plan("Apple") == ["task"]

    assert app.retrieve("Apple") == "context"

    assert app.analyze(foo="bar") == "analysis"

    assert app.audit("analysis") is True