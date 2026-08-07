"""
health.py

Health endpoints.
"""

from __future__ import annotations

from app.api.schemas import AnalyzeResponse


class HealthService:

    @staticmethod
    def check() -> dict:

        return {
            "status": "healthy",
            "service": "AI Financial Analyst",
        }