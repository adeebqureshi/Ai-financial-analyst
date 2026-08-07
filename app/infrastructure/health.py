"""
Health check.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class HealthStatus:

    status: str = "healthy"

    database: bool = True

    cache: bool = True

    vector_store: bool = True

    @property
    def ok(self) -> bool:

        return (
            self.database
            and self.cache
            and self.vector_store
        )