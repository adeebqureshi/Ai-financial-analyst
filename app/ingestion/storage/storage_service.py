"""
storage_service.py

High-level storage service for AI Financial Analyst.

Responsibilities
----------------
- Save SEC filings
- Save market data
- Save metadata
- Load stored data

This class hides all filesystem details from the
rest of the application.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.ingestion.storage.file_manager import FileManager
from app.ingestion.storage.path_manager import PathManager


class StorageService:
    """
    High-level storage service.
    """

    def __init__(self) -> None:

        self.paths = PathManager()

    ####################################################################
    # SEC
    ####################################################################

    def save_sec_filing(
        self,
        ticker: str,
        year: int,
        form_type: str,
        html: str,
    ) -> Path:
        """
        Save SEC filing.

        Example

        storage/raw/sec/AAPL/2024/10-K.html
        """

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

    ####################################################################
    # Market
    ####################################################################

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

    ####################################################################
    # Metadata
    ####################################################################

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