from __future__ import annotations

from dataclasses import dataclass

from app.comparison.company_metric import CompanyMetric


@dataclass(slots=True)
class ComparisonResult:

    metric: str

    companies: list[CompanyMetric]

    @property
    def winner(self) -> CompanyMetric:

        return max(
            self.companies,
            key=lambda x: x.value,
        )