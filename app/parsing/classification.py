"""
Financial section classification model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SectionClassification:
    """
    Classification result for a document section.
    """

    section_title: str
    category: str
    confidence: float

    @property
    def is_confident(self) -> bool:
        return self.confidence >= 0.8