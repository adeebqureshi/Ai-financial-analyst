"""
Workflow result model.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.agents.report import InvestmentReport


@dataclass(slots=True)
class WorkflowResult:
    """
    Final workflow output.
    """

    report: InvestmentReport

    success: bool

    @property
    def company(self) -> str:
        return self.report.company