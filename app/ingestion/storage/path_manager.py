from __future__ import annotations
from pathlib import Path
from app.utils.tickers import normalize_ticker
class PathManager:
    def __init__(self) -> None:
        self.project_root = Path(__file__).resolve().parents[3]
        self.storage_root = self.project_root / "storage"
        self.raw_root = self.storage_root / "raw"
        self.sec_root = self.raw_root / "sec"
        self.market_root = self.raw_root / "market"
        self.parsed_root = self.storage_root / "parsed"
        self.metadata_root = self.storage_root / "metadata"
        self.cache_root = self.storage_root / "cache"
        self.embedding_root = self.storage_root / "embeddings"
        self.report_root = self.storage_root / "reports"
    @staticmethod
    def ensure_directory(path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        return path
    def get_storage_root(self) -> Path:
        return self.ensure_directory(self.storage_root)
    def get_raw_root(self) -> Path:
        return self.ensure_directory(self.raw_root)
    def get_sec_path(
        self,
        ticker: str,
        year: int,
    ) -> Path:
        ticker = normalize_ticker(ticker)
        path = self.sec_root / ticker / str(year)
        return self.ensure_directory(path)
    def get_market_path(
        self,
        ticker: str,
    ) -> Path:
        ticker = normalize_ticker(ticker)
        path = self.market_root / ticker
        return self.ensure_directory(path)
    def get_parsed_path(
        self,
        ticker: str,
    ) -> Path:
        ticker = normalize_ticker(ticker)
        path = self.parsed_root / ticker
        return self.ensure_directory(path)
    def get_metadata_path(self) -> Path:
        return self.ensure_directory(self.metadata_root)
    def get_cache_path(self) -> Path:
        return self.ensure_directory(self.cache_root)
    def get_embedding_path(self) -> Path:
        return self.ensure_directory(self.embedding_root)
    def get_report_path(self) -> Path:
        return self.ensure_directory(self.report_root)