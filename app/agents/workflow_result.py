"""
Workflow result model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.agents.audit_result import AuditResult
from app.agents.report import InvestmentReport


@dataclass(slots=True)
class WorkflowResult:
    """
    Final workflow output.

    Attributes:
        report: The generated investment report (body holds the answer).
        success: Whether the audit passed.
        message: The answer text (same as ``report.body``).
        model: LLM model used for the answer.
        sources: Document chunks actually retrieved.
        plan: High-level execution steps that actually ran.
        tools_used: Tool execution metadata for the UI.
        intents: Detected intents.
        tickers: Tickers referenced by the answer.
        audit: The audit result.
    """

    report: InvestmentReport

    success: bool

    message: str = ""

    model: str | None = None

    sources: list[dict[str, Any]] = field(default_factory=list)

    plan: list[str] = field(default_factory=list)

    tools_used: list[dict[str, Any]] = field(default_factory=list)

    intents: list[str] = field(default_factory=list)

    tickers: list[str] = field(default_factory=list)

    audit: AuditResult | None = None

    @property
    def company(self) -> str:
        return self.report.company
