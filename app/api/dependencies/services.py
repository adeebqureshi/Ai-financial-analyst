"""
Service Dependency Injection

This module provides FastAPI dependency callables for injecting service
instances into route handlers. Each service is constructed with the
application ``Settings`` and yielded for the duration of the request.

Design Decisions:
    - **Factory functions, not globals**: Services are instantiated
      per-request via dependency factories. This ensures clean state
      between requests and makes services mockable in tests via
      ``app.dependency_overrides``.
    - **Settings injected into services**: Services receive ``Settings``
      as a constructor argument, satisfying the Dependency Inversion
      Principle — services depend on an abstraction (``Settings``),
      not a concrete singleton.
    - **Yield-based**: Using ``yield`` allows cleanup logic (if needed)
      after the request completes.

Usage in a route::

    from fastapi import Depends
    from app.api.dependencies.services import get_health_service
    from app.services.health_service import HealthService

    @router.get("/health")
    async def health(service: HealthService = Depends(get_health_service)):
        return service.check_health()
"""

from __future__ import annotations

from collections.abc import Iterator

from app.core.config import Settings, get_settings
from app.services.health_service import HealthService
from app.services.version_service import VersionService


def get_health_service(
    settings: Settings | None = None,
) -> Iterator[HealthService]:
    """
    FastAPI dependency that yields a ``HealthService`` instance.

    Args:
        settings: Optional ``Settings`` instance. If ``None``, the
            singleton from ``get_settings()`` is used.

    Yields:
        A ``HealthService`` instance configured with the given settings.
    """
    if settings is None:
        settings = get_settings()
    service = HealthService(settings)
    yield service


def get_version_service(
    settings: Settings | None = None,
) -> Iterator[VersionService]:
    """
    FastAPI dependency that yields a ``VersionService`` instance.

    Args:
        settings: Optional ``Settings`` instance. If ``None``, the
            singleton from ``get_settings()`` is used.

    Yields:
        A ``VersionService`` instance configured with the given settings.
    """
    if settings is None:
        settings = get_settings()
    service = VersionService(settings)
    yield service