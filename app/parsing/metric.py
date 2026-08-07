"""
Financial metric model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FinancialMetric:
    """
    Represents one extracted financial metric.
    """

    name: str
    value: str
    source: str

    @property
    def numeric(self) -> float | None:

        value = (
            self.value.replace(",", "")
            .replace("$", "")
            .strip()
        )

        try:
            return float(value)
        except ValueError:
            return None