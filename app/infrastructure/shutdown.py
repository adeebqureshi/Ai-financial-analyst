"""
Application shutdown.

Disposes every infrastructure connection held by the container. Each step is
best-effort: shutdown must never raise, or worker recycling (SIGTERM handling
under gunicorn/uvicorn) would log spurious failures.
"""

from __future__ import annotations

from app.infrastructure.container import Container


def shutdown(
    container: Container,
) -> None:

    container.close()