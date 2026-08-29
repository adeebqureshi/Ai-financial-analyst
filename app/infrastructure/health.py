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
        """
        Critical-component readiness.

        The Redis cache is deliberately excluded: it is an optional
        accelerator and every consumer (rate limiter, chat store) already
        falls back to the database when Redis is unavailable.
        """
        return self.database and self.vector_store