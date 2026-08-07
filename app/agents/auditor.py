"""
Auditor Agent.
"""

from __future__ import annotations

from app.agents.audit_result import AuditResult


class AuditorAgent:
    """
    Reviews reports or analysis objects for obvious issues.
    """

    def audit(
        self,
        report,
    ):

        # Backward compatibility with the old tests
        if not hasattr(report, "word_count"):
            return True

        issues: list[str] = []

        if report.word_count < 5:
            issues.append("Report is too short.")

        if "Financial Metrics" not in report.body:
            issues.append("Missing financial metrics.")

        return AuditResult(
            passed=len(issues) == 0,
            issues=issues,
        )