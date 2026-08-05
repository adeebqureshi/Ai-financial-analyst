"""
base_parser.py

Abstract parser interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class BaseParser(ABC):
    """
    Base interface for all document parsers.
    """

    @abstractmethod
    def parse_file(
        self,
        file_path: Path,
    ) -> str:
        """
        Parse a document from disk.

        Returns
        -------
        str
            Parsed markdown/text.
        """

    @abstractmethod
    def parse_text(
        self,
        text: str,
    ) -> str:
        """
        Parse raw document text.

        Returns
        -------
        str
        """