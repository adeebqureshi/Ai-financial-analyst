"""
Planner agent.
"""

from __future__ import annotations

from app.agents.task import Task


class PlannerAgent:
    """
    Plans the sequence of tasks needed
    to answer a user request.
    """

    def plan(
        self,
        query: str,
    ) -> list[Task]:

        tasks: list[Task] = []

        query = query.lower()

        if any(
            keyword in query
            for keyword in (
                "valuation",
                "dcf",
                "intrinsic value",
            )
        ):
            tasks.append(
                Task(
                    name="Retrieve Documents",
                    description="Retrieve relevant financial documents.",
                )
            )

            tasks.append(
                Task(
                    name="Run Valuation",
                    description="Perform DCF valuation.",
                )
            )

            tasks.append(
                Task(
                    name="Generate Report",
                    description="Generate valuation report.",
                )
            )

            return tasks

        tasks.append(
            Task(
                name="Retrieve Documents",
                description="Retrieve relevant financial documents.",
            )
        )

        tasks.append(
            Task(
                name="Generate Report",
                description="Generate final response.",
            )
        )

        return tasks