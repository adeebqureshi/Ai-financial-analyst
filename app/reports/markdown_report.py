"""
markdown_report.py

Markdown report generator.
"""

from __future__ import annotations

from app.reports.report_models import Report


class MarkdownReport:

    @staticmethod
    def generate(
        result: dict,
    ) -> Report:

        company = result["company"]
        market = result["market"]
        analysis = result["analysis"]

        content = f"""# Financial Analysis Report

## Company

**Name:** {company.name}

**Ticker:** {company.ticker}

---

## Market

Current Price: {market.current_price:.2f} {market.currency}

---

## Valuation

Intrinsic Value: {analysis.intrinsic_value:.2f}

Upside: {analysis.upside:.2f}%

Recommendation: {analysis.recommendation}

---

## Financial Health

Health Score: {analysis.health_score}

Rating: {analysis.health_rating}

Piotroski: {analysis.piotroski_score}

Altman Z: {analysis.altman_score:.2f}

Beneish M: {analysis.beneish_score:.2f}
"""

        return Report(
            title=f"{company.ticker} Financial Report",
            ticker=company.ticker,
            content=content,
        )