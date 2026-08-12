"""
coordinator.py

Coordinator Agent — the orchestrator for the agentic research pipeline.

Flow::

    user question
        -> planner (intent + minimal tool selection, pronoun resolution)
        -> tool executor (runs the existing services)
        -> collect evidence + sources
        -> financial analyst (evidence-grounded synthesis)
        -> auditor (grounding / ticker-isolation / no-fabrication checks)
        -> final answer + sources + tool-transparency metadata

The coordinator never runs tools speculatively: it executes exactly the tool
calls the planner selected, and never fabricates a result when a tool fails.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from app.agents.auditor import AuditorAgent
from app.agents.financial_analyst import FinancialAnalystAgent
from app.agents.memory import ConversationMemory
from app.agents.planner import PlannerAgent
from app.agents.report import InvestmentReport
from app.agents.report_writer_v2 import ReportWriterAgent
from app.agents.research_plan import ResearchPlan
from app.agents.tools import ToolRegistry
from app.agents.workflow_result import WorkflowResult
from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _async_model_name(analyst: Any) -> str | None:
    """
    Best-effort model name for the streaming synthesis.

    Reads the model off the analyst's async provider. Returns ``None`` when the
    analyst does not expose an async client (e.g. injected test doubles).
    """
    ensure = getattr(analyst, "ensure_async_client", None)

    if not callable(ensure):
        return None

    try:
        provider = ensure().provider
    except Exception:
        return None

    return getattr(provider, "MODEL", None)

_AUDITOR_NOTE = (
    "\n\n_Auditor note: this response could not be fully verified against "
    "retrieved evidence. Please verify the claims before relying on them._"
)


class CoordinatorAgent:
    """
    Coordinates the complete agentic financial research workflow.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        tools: ToolRegistry | None = None,
        analyst: FinancialAnalystAgent | None = None,
        auditor: AuditorAgent | None = None,
        report_writer: ReportWriterAgent | None = None,
    ) -> None:
        settings = settings or get_settings()

        self._settings = settings

        self.planner = PlannerAgent()

        self._memory = ConversationMemory()
        self.planner.memory = self._memory

        self.tools = tools or ToolRegistry(settings)

        self.analyst = analyst or FinancialAnalystAgent(settings)

        self.auditor = auditor or AuditorAgent()

        self.report_writer = report_writer or ReportWriterAgent()

    def run(
        self,
        query: str,
        ticker: str | None = None,
        document_id: str | None = None,
        session_id: str | None = None,
    ) -> WorkflowResult:
        """
        Execute the full agentic pipeline for a single question.

        Args:
            query: The user question.
            ticker: Optional explicit ticker context.
            document_id: Optional document the question is scoped to.
            session_id: Optional session id for follow-up context.

        Returns:
            A :class:`WorkflowResult` with the answer, sources and the tools
            that actually ran.
        """
        plan = self.planner.plan(
            query=query,
            ticker=ticker,
            document_id=document_id,
            session_id=session_id,
        )

        evidence, steps, tools_used, sources = self._execute(plan)

        answer, model = self._synthesize(plan, evidence, sources)

        audit = self.auditor.audit_evidence(
            plan=plan,
            evidence=evidence,
            answer=answer,
            sources=sources,
            model=model,
        )

        if not audit.passed:
            answer = f"{answer}{_AUDITOR_NOTE}"

        if session_id:
            self._memory.remember(
                session_id,
                plan.tickers,
                query,
                answer,
            )

        company = plan.tickers[0] if plan.tickers else "Research"

        report = InvestmentReport(
            company=company,
            title=f"{company} Research",
            body=answer,
        )

        return WorkflowResult(
            report=report,
            success=audit.passed,
            message=answer,
            model=model,
            sources=sources,
            plan=steps,
            tools_used=tools_used,
            intents=[intent.value for intent in plan.intents],
            tickers=plan.tickers,
            audit=audit,
        )

    def run_report(
        self,
        query: str,
        ticker: str | None = None,
        document_id: str | None = None,
        session_id: str | None = None,
    ) -> WorkflowResult:
        """
        Execute the full agentic pipeline and generate a structured investment report.

        This is used when the user explicitly requests a report (REPORT_GENERATION intent).

        Args:
            query: The user question/request.
            ticker: Optional explicit ticker context.
            document_id: Optional document the question is scoped to.
            session_id: Optional session id for follow-up context.

        Returns:
            A :class:`WorkflowResult` with the structured report, sources and tools.
        """
        plan = self.planner.plan(
            query=query,
            ticker=ticker,
            document_id=document_id,
            session_id=session_id,
        )

        evidence, steps, tools_used, sources = self._execute(plan)

        # Generate the structured report using the ReportWriterAgent
        report_content, model = self.report_writer.write(
            query=plan.query,
            intents=plan.intents,
            evidence=evidence,
            sources=sources,
            tickers=plan.tickers,
        )

        # Audit the report content
        audit = self.auditor.audit_evidence(
            plan=plan,
            evidence=evidence,
            answer=report_content,
            sources=sources,
            model=model,
        )

        if not audit.passed:
            report_content = f"{report_content}{_AUDITOR_NOTE}"

        if session_id:
            self._memory.remember(
                session_id,
                plan.tickers,
                query,
                report_content,
            )

        company = plan.tickers[0] if plan.tickers else "Research"

        report = InvestmentReport(
            company=company,
            title=f"{company} Investment Research Report",
            body=report_content,
        )

        return WorkflowResult(
            report=report,
            success=audit.passed,
            message=report_content,
            model=model,
            sources=sources,
            plan=steps,
            tools_used=tools_used,
            intents=[intent.value for intent in plan.intents],
            tickers=plan.tickers,
            audit=audit,
        )

    async def stream_run(
        self,
        query: str,
        ticker: str | None = None,
        document_id: str | None = None,
        session_id: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Execute the agentic pipeline and stream the synthesized answer.

        The planning and tool execution phases run to completion first (they
        are synchronous, real-data operations); only the final LLM synthesis is
        streamed progressively. This keeps the response evidence-grounded while
        giving the client progressive output.

        Args:
            query: The user question.
            ticker: Optional explicit ticker context.
            document_id: Optional document the question is scoped to.
            session_id: Optional session id for follow-up context.

        Yields:
            A sequence of event dicts:
            - ``{"type": "plan", ...}``   — planning / tool metadata.
            - ``{"type": "token", "delta": ...}`` — a text delta.
            - ``{"type": "done", ...}``   — the final result.
            - ``{"type": "error", "message": ...}`` — a pipeline failure.
        """
        try:
            plan = self.planner.plan(
                query=query,
                ticker=ticker,
                document_id=document_id,
                session_id=session_id,
            )

            evidence, steps, tools_used, sources = self._execute(plan)
        except Exception as exc:
            logger.warning(
                "Streaming pipeline failed before synthesis: %s",
                exc,
            )
            yield {
                "type": "error",
                "message": "Research failed before the answer could be generated.",
            }
            return

        yield {
            "type": "plan",
            "tickers": plan.tickers,
            "intents": [intent.value for intent in plan.intents],
            "steps": steps,
            "tools_used": tools_used,
        }

        usable = {
            tool: results
            for tool, results in evidence.items()
            if any(r.status == "done" and r.result for r in results)
        }

        buffer: list[str] = []

        async for delta in self.analyst.stream_synthesize(
            query=plan.query,
            intents=plan.intents,
            evidence=usable,
            sources=sources,
            tickers=plan.tickers,
        ):
            buffer.append(delta)
            yield {"type": "token", "delta": delta}

        answer = "".join(buffer)

        model = _async_model_name(self.analyst)

        audit = self.auditor.audit_evidence(
            plan=plan,
            evidence=evidence,
            answer=answer,
            sources=sources,
            model=model,
        )

        if not audit.passed:
            answer = f"{answer}{_AUDITOR_NOTE}"
            yield {"type": "token", "delta": _AUDITOR_NOTE}

        if session_id:
            self._memory.remember(
                session_id,
                plan.tickers,
                query,
                answer,
            )

        yield {
            "type": "done",
            "message": answer,
            "model": model,
            "success": audit.passed,
            "tickers": plan.tickers,
            "intents": [intent.value for intent in plan.intents],
            "sources": sources,
            "steps": steps,
            "tools_used": tools_used,
        }

    # ──────────────────────────────────────────────────────────────────
    # Internal pipeline
    # ──────────────────────────────────────────────────────────────────

    def _execute(
        self,
        plan: ResearchPlan,
    ) -> tuple[dict[str, Any], list[str], list[dict[str, str]], list[dict[str, Any]]]:
        """
        Run the planned tool calls, collecting evidence and sources.

        Returns:
            ``(evidence, steps, tools_used, sources)``.
        """
        evidence: dict[str, Any] = {}
        steps: list[str] = []
        tools_used: list[dict[str, str]] = []
        sources: list[dict[str, Any]] = []

        for call in plan.tools:
            result = self.tools.execute(call.tool, call.args)

            evidence.setdefault(call.tool, []).append(result)

            steps.append(call.label or call.tool)

            tools_used.append({
                "tool": call.tool,
                "status": result.status,
                "detail": result.detail or call.label or call.tool,
            })

            if call.tool == "search_documents" and result.status == "done" and result.result:
                sources.extend(result.result.get("chunks", []))

        return evidence, steps, tools_used, sources

    def _synthesize(
        self,
        plan: ResearchPlan,
        evidence: dict[str, Any],
        sources: list[dict[str, Any]],
    ) -> tuple[str, str | None]:
        """
        Generate the final answer from the collected evidence.

        When no evidence was collected (no tools ran or all failed) the
        analyst returns the insufficient-evidence message — nothing is
        fabricated.
        """
        usable = {
            tool: results
            for tool, results in evidence.items()
            if any(r.status == "done" and r.result for r in results)
        }

        answer, model = self.analyst.synthesize(
            query=plan.query,
            intents=plan.intents,
            evidence=usable,
            sources=sources,
            tickers=plan.tickers,
        )

        return answer, model
