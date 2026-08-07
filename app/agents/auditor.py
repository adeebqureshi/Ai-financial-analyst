"""
auditor.py

Auditor agent responsible for validating analysis results.
"""

from __future__ import annotations


class AuditorAgent:
    """
    Performs basic validation of analysis results.
    """

    def audit(
        self,
        analysis,
    ) -> bool:

        required = (
            "intrinsic_value",
            "recommendation",
            "health_score",
        )

        return all(
            hasattr(analysis, field)
            for field in required
        )