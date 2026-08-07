"""
Rule-based financial section classifier.
"""

from __future__ import annotations

from app.parsing.classification import SectionClassification
from app.parsing.section import Section


class SectionClassifier:

    RULES = {
        "Risk Factors": [
            "risk",
            "risk factors",
        ],
        "MD&A": [
            "management discussion",
            "md&a",
        ],
        "Business": [
            "business",
            "overview",
        ],
        "Balance Sheet": [
            "balance sheet",
        ],
        "Income Statement": [
            "income statement",
            "statement of operations",
        ],
        "Cash Flow": [
            "cash flow",
            "cash flows",
        ],
        "Notes": [
            "notes",
            "notes to",
        ],
    }

    def classify(
        self,
        sections: list[Section],
    ) -> list[SectionClassification]:

        results: list[SectionClassification] = []

        for section in sections:

            title = section.title.lower()

            category = "Other"

            confidence = 0.50

            for label, keywords in self.RULES.items():

                if any(keyword in title for keyword in keywords):

                    category = label
                    confidence = 0.95
                    break

            results.append(
                SectionClassification(
                    section_title=section.title,
                    category=category,
                    confidence=confidence,
                )
            )

        return results