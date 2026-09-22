from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
class BaseParser(ABC):
    @abstractmethod
    def parse_file(
        self,
        file_path: Path,
    ) -> str:
    @abstractmethod
    def parse_text(
        self,
        text: str,
    ) -> str: