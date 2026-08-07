"""
Application shutdown.
"""

from __future__ import annotations

from app.infrastructure.container import Container


def shutdown(
    container: Container,
) -> None:

    container.database.dispose()