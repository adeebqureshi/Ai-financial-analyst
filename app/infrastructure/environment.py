"""
Environment helpers.
"""

from __future__ import annotations

from app.infrastructure.config import Settings


class Environment:

    def __init__(self) -> None:

        self.settings = Settings()

    @property
    def is_development(self) -> bool:

        return self.settings.environment == "development"

    @property
    def is_production(self) -> bool:

        return self.settings.environment == "production"