"""
Settings Dependency Injection

This module provides FastAPI dependency callables for injecting the
application ``Settings`` singleton into route handlers.

Design Decisions:
    - **``Depends()`` over global access**: Using FastAPI's dependency
      injection system instead of calling ``get_settings()`` directly in
      route handlers makes the dependency explicit, testable, and
      overridable per-endpoint via ``app.dependency_overrides``.
    - **Yield-based dependency**: Using ``yield`` ensures the settings
      cache is cleared after the request, preventing state leakage in
      tests. In production, the singleton is cached and the clear is a
      no-op.
    - **Separate from service dependencies**: Settings injection is a
      cross-cutting concern distinct from service instantiation, so it
      lives in its own module.
"""

from __future__ import annotations

from collections.abc import Iterator

from app.core.config import Settings, get_settings


def get_settings_dep() -> Iterator[Settings]:
    """
    FastAPI dependency that yields the application settings singleton.

    Usage in a route::

        from fastapi import Depends
        from app.api.dependencies.settings import get_settings_dep
        from app.core.config import Settings

        @router.get("/example")
        async def example(settings: Settings = Depends(get_settings_dep)):
            return {"env": settings.environment}

    Yields:
        The cached ``Settings`` singleton instance.
    """
    settings = get_settings()
    yield settings