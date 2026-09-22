from __future__ import annotations
from app.core.config import Settings
from app.schemas.version import VersionResponse
class VersionService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
    def get_version_info(self) -> VersionResponse:
        return VersionResponse(
            app_name=self._settings.app_name,
            app_version=self._settings.app_version,
            demo_mode=self._settings.is_demo_mode,
        )