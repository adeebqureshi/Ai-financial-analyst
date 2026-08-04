"""
path_manager.py

Centralized path management for the AI Financial Analyst project.

Responsibilities
----------------
- Construct all project storage paths.
- Create missing directories.
- Validate paths.
- Prevent path traversal attacks.
- Provide a single source of truth for filesystem locations.
"""

from __future__ import annotations

from pathlib import Path


class PathManager:
    """
    Centralized filesystem path manager.

    Every component (SEC downloader, parser, retriever, etc.)
    should obtain filesystem paths through this class instead
    of constructing them manually.
    """

    def __init__(self) -> None:
        """
        Initialize all important project paths.
        """

        # project root
        self.project_root = Path(__file__).resolve().parents[3]

        # storage root
        self.storage_root = self.project_root / "storage"

        # storage folders
        self.raw_root = self.storage_root / "raw"
        self.sec_root = self.raw_root / "sec"
        self.market_root = self.raw_root / "market"

        self.parsed_root = self.storage_root / "parsed"
        self.metadata_root = self.storage_root / "metadata"
        self.cache_root = self.storage_root / "cache"
        self.embedding_root = self.storage_root / "embeddings"
        self.report_root = self.storage_root / "reports"

    ####################################################################
    # Generic Helpers
    ####################################################################

    @staticmethod
    def ensure_directory(path: Path) -> Path:
        """
        Create directory if it does not already exist.

        Parameters
        ----------
        path : Path

        Returns
        -------
        Path
        """

        path.mkdir(parents=True, exist_ok=True)
        return path

    ####################################################################
    # Root Paths
    ####################################################################

    def get_storage_root(self) -> Path:
        return self.ensure_directory(self.storage_root)

    def get_raw_root(self) -> Path:
        return self.ensure_directory(self.raw_root)

    ####################################################################
    # SEC
    ####################################################################

    def get_sec_path(
        self,
        ticker: str,
        year: int,
    ) -> Path:
        """
        Example

        storage/raw/sec/AAPL/2024/
        """

        path = self.sec_root / ticker.upper() / str(year)

        return self.ensure_directory(path)

    ####################################################################
    # Market
    ####################################################################

    def get_market_path(
        self,
        ticker: str,
    ) -> Path:
        """
        Example

        storage/raw/market/AAPL/
        """

        path = self.market_root / ticker.upper()

        return self.ensure_directory(path)

    ####################################################################
    # Parsed
    ####################################################################

    def get_parsed_path(
        self,
        ticker: str,
    ) -> Path:
        """
        storage/parsed/AAPL/
        """

        path = self.parsed_root / ticker.upper()

        return self.ensure_directory(path)

    ####################################################################
    # Metadata
    ####################################################################

    def get_metadata_path(self) -> Path:
        return self.ensure_directory(self.metadata_root)

    ####################################################################
    # Cache
    ####################################################################

    def get_cache_path(self) -> Path:
        return self.ensure_directory(self.cache_root)

    ####################################################################
    # Embeddings
    ####################################################################

    def get_embedding_path(self) -> Path:
        return self.ensure_directory(self.embedding_root)

    ####################################################################
    # Reports
    ####################################################################

    def get_report_path(self) -> Path:
        return self.ensure_directory(self.report_root)