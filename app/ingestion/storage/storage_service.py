from __future__ import annotations
from pathlib import Path
from typing import Any
from app.ingestion.storage.file_manager import FileManager
from app.ingestion.storage.path_manager import PathManager
class StorageService:
    def __init__(self) -> None:
        self.paths = PathManager()
    def save_sec_filing(
        self,
        ticker: str,
        year: int,
        form_type: str,
        html: str,
    ) -> Path:
        directory = self.paths.get_sec_path(
            ticker,
            year,
        )
        file = directory / f"{form_type}.html"
        FileManager.save_text(
            file,
            html,
        )
        return file
    def load_sec_filing(
        self,
        ticker: str,
        year: int,
        form_type: str,
    ) -> str:
        directory = self.paths.get_sec_path(
            ticker,
            year,
        )
        file = directory / f"{form_type}.html"
        return FileManager.load_text(file)
    def save_market_data(
        self,
        ticker: str,
        data: dict[str, Any],
    ) -> Path:
        directory = self.paths.get_market_path(
            ticker,
        )
        file = directory / "market.json"
        FileManager.save_json(
            file,
            data,
        )
        return file
    def load_market_data(
        self,
        ticker: str,
    ) -> dict[str, Any]:
        directory = self.paths.get_market_path(
            ticker,
        )
        file = directory / "market.json"
        return FileManager.load_json(file)
    def save_metadata(
        self,
        filename: str,
        metadata: dict[str, Any],
    ) -> Path:
        directory = self.paths.get_metadata_path()
        file = directory / filename
        FileManager.save_json(
            file,
            metadata,
        )
        return file
    def load_metadata(
        self,
        filename: str,
    ) -> dict[str, Any]:
        directory = self.paths.get_metadata_path()
        file = directory / filename
        return FileManager.load_json(file)