"""
research_plan.py

Plan model produced by the planner agent.

A plan captures the intents, tickers and — crucially — the *minimal* ordered
set of tool calls required to answer a question. The coordinator executes
exactly these tool calls; no tool is ever run speculatively.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.agents.intents import AgentIntent
from app.agents.task import Task


@dataclass(slots=True)
class ToolCall:
    """
    A single tool invocation the executor should perform.

    Attributes:
        tool: The tool name (see ``app.agents.tools`` registry).
        args: Keyword arguments for the tool.
        label: Human-readable step shown to the user (never chain-of-thought).
    """

    tool: str
    args: dict[str, object] = field(default_factory=dict)
    label: str = ""


@dataclass(slots=True)
class ResearchPlan:
    """
    The planner's output: what to run, in what order.

    Attributes:
        query: The (possibly resolved) user question.
        intents: Detected agent intents.
        tickers: Tickers the plan will operate on.
        tools: Ordered tool calls to execute.
        needs_rag: Whether document retrieval is part of the plan.
        reasoning: Brief planner rationale (safe, high-level steps only).
    """

    query: str
    intents: list[AgentIntent] = field(default_factory=list)
    tickers: list[str] = field(default_factory=list)
    tools: list[ToolCall] = field(default_factory=list)
    needs_rag: bool = False
    reasoning: list[str] = field(default_factory=list)

    @property
    def tool_names(self) -> list[str]:
        """The names of the tools selected by the planner, in order."""
        return [call.tool for call in self.tools]

    @property
    def tasks(self) -> list[Task]:
        """Human-readable task list (kept for pipeline compatibility)."""
        return [
            Task(
                name=call.tool,
                description=call.label,
            )
            for call in self.tools
        ]
