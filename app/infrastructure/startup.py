"""
Application startup.
"""

from __future__ import annotations

from app.infrastructure.container import Container


def startup() -> Container:

    return Container()