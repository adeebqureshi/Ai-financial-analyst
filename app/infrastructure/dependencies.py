"""
Dependency providers.
"""

from __future__ import annotations

from app.infrastructure.container import Container

_container = Container()


def get_container() -> Container:

    return _container