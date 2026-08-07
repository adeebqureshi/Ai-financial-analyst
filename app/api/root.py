"""
root.py

Root endpoint service.
"""

from __future__ import annotations


class RootService:

    @staticmethod
    def info() -> dict:

        return {
            "application": "AI Financial Analyst",
            "status": "running",
            "version": "1.0.0",
        }