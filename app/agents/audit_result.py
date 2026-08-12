"""
Audit result model.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AuditResult:
    """
    Result of auditing an investment report.

    Attributes:
        passed: ``True`` when no grounding violation was found.
        issues: Hard violations (fabricated figures, unscoped tickers,
            unretrieved citations, failed sandbox calculations).
        notes: Non-blocking provenance notes (e.g. that a figure was computed
            by the sandbox rather than asserted by the LLM).
    """

    passed: bool
    issues: list[str]
    notes: list[str] = field(default_factory=list)

    @property
    def issue_count(self) -> int:
        return len(self.issues)
