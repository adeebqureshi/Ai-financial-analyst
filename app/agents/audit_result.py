"""
Audit result model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AuditResult:
    """
    Result of auditing an investment report.
    """

    passed: bool
    issues: list[str]

    @property
    def issue_count(self) -> int:
        return len(self.issues)