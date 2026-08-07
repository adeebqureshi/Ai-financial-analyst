from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CompanyMetric:

    company: str

    value: float