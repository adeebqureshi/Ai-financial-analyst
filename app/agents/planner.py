"""
planner.py

Planning agent.
"""

from __future__ import annotations

from app.agents.models import AgentTask


class PlannerAgent:

    def plan(
        self,
        query: str,
    ) -> list[AgentTask]:

        tasks = []

        q = query.lower()

        if any(
            word in q
            for word in [
                "valuation",
                "intrinsic",
                "dcf",
            ]
        ):
            tasks.append(
                AgentTask(
                    "valuation",
                    "Perform company valuation.",
                )
            )

        if any(
            word in q
            for word in [
                "risk",
                "bankruptcy",
                "health",
            ]
        ):
            tasks.append(
                AgentTask(
                    "health",
                    "Evaluate financial health.",
                )
            )

        if any(
            word in q
            for word in [
                "revenue",
                "profit",
                "growth",
            ]
        ):
            tasks.append(
                AgentTask(
                    "analysis",
                    "Analyze financial performance.",
                )
            )

        if not tasks:

            tasks.append(
                AgentTask(
                    "general",
                    "General financial analysis.",
                )
            )

        return tasks