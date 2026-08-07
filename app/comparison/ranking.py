from __future__ import annotations

from app.comparison.company_metric import CompanyMetric


class CompanyRanking:

    def rank(
        self,
        metrics: list[CompanyMetric],
    ) -> list[CompanyMetric]:

        return sorted(
            metrics,
            key=lambda x: x.value,
            reverse=True,
        )