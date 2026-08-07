"""
version.py

Version information.
"""

from __future__ import annotations


class VersionService:

    VERSION = "1.0.0"

    @classmethod
    def get(cls) -> dict:

        return {
            "application": "AI Financial Analyst",
            "version": cls.VERSION,
        }