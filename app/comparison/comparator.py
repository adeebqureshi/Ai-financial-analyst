from __future__ import annotations

from app.comparison.company_metric import CompanyMetric
from app.comparison.comparison_result import ComparisonResult
from app.comparison.ranking import CompanyRanking


class CompanyComparator:

    def __init__(self):

        self.ranking = CompanyRanking()

    def compare(
        self,
        metric: str,
        companies: list[CompanyMetric],
    ) -> ComparisonResult:

        ranked = self.ranking.rank(
            companies,
        )

        return ComparisonResult(
            metric=metric,
            companies=ranked,
        )