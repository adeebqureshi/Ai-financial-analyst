from app.agents.audit_result import AuditResult
from app.agents.auditor import AuditorAgent
from app.agents.intents import AgentIntent
from app.agents.research_plan import ResearchPlan, ToolCall
from app.agents.tools import ToolResult


def _plan(tool_names: list[str], tickers: list[str]) -> ResearchPlan:
    return ResearchPlan(
        query="test",
        intents=[AgentIntent.VALUATION],
        tickers=tickers,
        tools=[ToolCall(tool=name, args={}) for name in tool_names],
        needs_rag="search_documents" in tool_names,
    )


def _result(tool: str, payload: dict | None, status: str = "done") -> ToolResult:
    return ToolResult(
        tool=tool,
        status=status,
        detail=tool,
        result=payload,
    )


def _audit(plan, evidence, answer, sources=None):
    return AuditorAgent().audit_evidence(
        plan=plan,
        evidence=evidence,
        answer=answer,
        sources=sources or [],
    )


def test_audit_passes_for_grounded_answer():
    plan = _plan(["calculate_valuation"], ["AAPL"])

    evidence = {
        "calculate_valuation": [
            _result("calculate_valuation", {"ticker": "AAPL", "intrinsic_value": 250.0})
        ]
    }

    audit = _audit(plan, evidence, "AAPL intrinsic value is 250.")

    assert audit.passed


def test_audit_flags_ticker_leak():
    plan = _plan(["get_financials"], ["AAPL"])

    evidence = {
        "get_financials": [
            _result("get_financials", {"ticker": "MSFT"})
        ]
    }

    audit = _audit(plan, evidence, "AAPL analysis")

    assert not audit.passed

    assert any("MSFT" in issue for issue in audit.issues)


def test_audit_flags_citation_not_retrieved():
    plan = _plan(["search_documents"], ["AAPL"])

    evidence = {
        "search_documents": [
            _result(
                "search_documents",
                {
                    "chunks": [
                        {
                            "document_id": "doc1",
                            "filename": "Apple 10-K.pdf",
                            "page": 42,
                            "text": "risk",
                        }
                    ]
                },
            )
        ]
    }

    sources = evidence["search_documents"][0].result["chunks"]

    answer = "According to Apple 10-K.pdf (page 99), Apple faces risk."

    audit = _audit(plan, evidence, answer, sources=sources)

    assert not audit.passed

    assert any("page 99" in issue for issue in audit.issues)


def test_audit_allows_citation_matching_retrieved_chunk():
    plan = _plan(["search_documents"], ["AAPL"])

    chunk = {
        "document_id": "doc1",
        "filename": "Apple 10-K.pdf",
        "page": 42,
        "text": "risk",
    }

    evidence = {
        "search_documents": [
            _result("search_documents", {"chunks": [chunk]})
        ]
    }

    answer = "According to Apple 10-K.pdf (page 42), Apple faces risk."

    audit = _audit(plan, evidence, answer, sources=[chunk])

    assert audit.passed


def test_audit_notes_unsupported_recommendation():
    plan = _plan(["get_financials"], ["AAPL"])

    evidence = {
        "get_financials": [
            _result("get_financials", {"ticker": "AAPL"})
        ]
    }

    audit = _audit(plan, evidence, "AAPL is undervalued — you should buy.")

    # No valuation tool ran, so this is a warning, not a hard fabrication.
    assert audit.passed


def test_old_report_audit_still_works():
    from app.agents.report import InvestmentReport

    auditor = AuditorAgent()

    report = InvestmentReport(
        company="Apple",
        title="Apple Report",
        body="Financial Metrics\nRevenue increased.\nROE: 25%",
    )

    result = auditor.audit(report)

    assert isinstance(result, AuditResult)

    assert result.passed


def test_audit_passes_when_rag_returned_nothing():
    plan = _plan(["search_documents"], ["TSLA"])

    evidence = {
        "search_documents": [
            _result("search_documents", {"chunks": []})
        ]
    }

    audit = _audit(
        plan,
        evidence,
        "I couldn't find sufficient evidence to answer that question.",
    )

    assert audit.passed
