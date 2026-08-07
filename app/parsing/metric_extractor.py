"""
Financial metric extractor.
"""

from __future__ import annotations

import re

from app.parsing.metric import FinancialMetric


class MetricExtractor:
    """
    Extracts simple financial metrics from text.
    """

    PATTERNS = {
        "Revenue": re.compile(
            r"Revenue\s*[:\-]?\s*\$?([\d,]+(?:\.\d+)?)",
            re.IGNORECASE,
        ),
        "Net Income": re.compile(
            r"Net Income\s*[:\-]?\s*\$?([\d,]+(?:\.\d+)?)",
            re.IGNORECASE,
        ),
        "EPS": re.compile(
            r"EPS\s*[:\-]?\s*\$?([\d,]+(?:\.\d+)?)",
            re.IGNORECASE,
        ),
        "Assets": re.compile(
            r"Assets\s*[:\-]?\s*\$?([\d,]+(?:\.\d+)?)",
            re.IGNORECASE,
        ),
        "Liabilities": re.compile(
            r"Liabilities\s*[:\-]?\s*\$?([\d,]+(?:\.\d+)?)",
            re.IGNORECASE,
        ),
    }

    def extract(
        self,
        text: str,
    ) -> list[FinancialMetric]:

        metrics: list[FinancialMetric] = []

        for name, pattern in self.PATTERNS.items():

            match = pattern.search(text)

            if match:

                metrics.append(
                    FinancialMetric(
                        name=name,
                        value=match.group(1),
                        source="regex",
                    )
                )

        return metrics