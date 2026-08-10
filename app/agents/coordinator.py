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

from typing import Any

from app.agents.audit_result import AuditResult
from app.agents.auditor import AuditorAgent
from app.agents.financial_analyst import FinancialAnalystAgent
from app.agents.memory import ConversationMemory
from app.agents.planner import PlannerAgent
from app.agents.report import InvestmentReport
from app.agents.research_plan import ResearchPlan
from app.agents.tools import ToolRegistry
from app.agents.workflow_result import WorkflowResult
from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

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
    ) -> None:
        settings = settings or get_settings()

        self._settings = settings

        self.planner = PlannerAgent()

        self._memory = ConversationMemory()
        self.planner.memory = self._memory

        self.tools = tools or ToolRegistry(settings)

        self.analyst = analyst or FinancialAnalystAgent(settings)

        self.auditor = auditor or AuditorAgent()

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
