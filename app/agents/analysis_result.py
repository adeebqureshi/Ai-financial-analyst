"""
Financial analysis result.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AnalysisResult:
    """
    Result produced by the Quant Agent.
    """

    company: str
    summary: str
    metrics: dict[str, float]

    @property
    def metric_count(self) -> int:
        return len(self.metrics)