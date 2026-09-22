from __future__ import annotations
from collections.abc import Iterator
from app.core.config import Settings, get_settings
def get_settings_dep() -> Iterator[Settings]:
    settings = get_settings()
    yield settings