"""
Auditor tests for sandboxed-calculation provenance.

The auditor must distinguish an LLM assert from a sandbox-computed value and
record that provenance on the AuditResult.
"""

from app.agents.audit_result import AuditResult
from app.agents.auditor import AuditorAgent
from app.agents.intents import AgentIntent
from app.agents.research_plan import ResearchPlan, ToolCall
from app.agents.tools import ToolResult


def _plan(query: str = "WACC") -> ResearchPlan:
    return ResearchPlan(
        query=query,
        intents=[AgentIntent.CALCULATION],
        tickers=["AAPL"],
        tools=[ToolCall(tool="run_calculation", args={})],
    )


def _calc_result(
    status: str = "done",
    payload_status: str = "computed",
    result_value=None,
    computed_by: str = "sandbox",
    code: str = "result = cost_of_equity",
) -> ToolResult:
    return ToolResult(
        tool="run_calculation",
        status=status,
        detail="Computed: WACC",
        result={
            "question": "WACC",
            "ticker": "AAPL",
            "status": payload_status,
            "result": result_value,
            "computed_by": computed_by,
            "code": code,
        },
    )


def _audit(evidence, answer):
    return AuditorAgent().audit_evidence(
        plan=_plan(),
        evidence=evidence,
        answer=answer,
        sources=[],
    )


def test_mark_issue_for_failed_calculation():
    evidence = {"run_calculation": [_calc_result(status="error")]}

    audit = _audit(evidence, "WACC is 11%.")

    assert isinstance(audit, AuditResult)
    assert not audit.passed
    assert any("calculation failed" in issue.lower() for issue in audit.issues)


def test_successful_calculation_adds_sandbox_provenance_note():
    evidence = {"run_calculation": [_calc_result(result_value=0.1115)]}

    audit = _audit(evidence, "WACC for AAPL is 11.15%.")

    assert audit.passed
    assert any("sandbox" in note.lower() for note in audit.notes)


def test_computed_number_is_grounded_in_evidence():
    evidence = {
        "get_financials": [
            ToolResult(
                tool="get_financials",
                status="done",
                detail="financials",
                result={
                    "ticker": "AAPL",
                    "beta": 1.2,
                    "statement": {"revenue": 394_328.0},
                },
            )
        ],
        "run_calculation": [
            _calc_result(
                result_value=0.1115,
                code="result = risk_free_rate + beta * (market_return - risk_free_rate)",
            )
        ],
    }

    audit = _audit(
        evidence,
        "AAPL's WACC is 11.15% using a beta of 1.2.",
    )

    # The value is produced by the sandbox, so the claim is grounded and no
    # fabrication is flagged.
    assert audit.passed


def test_invented_number_not_backed_by_sandbox_is_flagged():
    evidence = {"run_calculation": [_calc_result(result_value=0.1115)]}

    audit = _audit(
        evidence,
        "AAPL's WACC is 11.15% and the cost of equity is 99%.",
    )

    assert not audit.passed
    assert any("99.00%" in issue for issue in audit.issues)


def test_audit_result_notes_default_backwards_compatible():
    result = AuditResult(passed=True, issues=[])

    assert result.notes == []
    assert result.issue_count == 0
