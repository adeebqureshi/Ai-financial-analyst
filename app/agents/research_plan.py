from __future__ import annotations
from dataclasses import dataclass, field
from app.agents.intents import AgentIntent
from app.agents.task import Task
@dataclass(slots=True)
class ToolCall:
    tool: str
    args: dict[str, object] = field(default_factory=dict)
    label: str = ""
@dataclass(slots=True)
class ResearchPlan:
    query: str
    intents: list[AgentIntent] = field(default_factory=list)
    tickers: list[str] = field(default_factory=list)
    tools: list[ToolCall] = field(default_factory=list)
    needs_rag: bool = False
    reasoning: list[str] = field(default_factory=list)
    @property
    def tool_names(self) -> list[str]:
        return [call.tool for call in self.tools]
    @property
    def tasks(self) -> list[Task]:
        return [
            Task(
                name=call.tool,
                description=call.label,
            )
            for call in self.tools
        ]