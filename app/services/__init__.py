"""
Services Package

This package contains the business logic services for the AI Financial
Analyst API. Services encapsulate use-case orchestration and are injected
into routers via FastAPI's dependency injection system.

Submodules:
    - ``health_service``: Application health check logic.
    - ``version_service``: Version info retrieval logic.

Design Principle:
    Routers contain no business logic — they parse input, call a service,
    and format output. All domain logic lives here.
"""

from __future__ import annotations

from app.services.health_service import HealthService
from app.services.version_service import VersionService

__all__ = [
    "HealthService",
    "VersionService",
]