"""
checksum.py

Checksum utilities for AI Financial Analyst.

Responsibilities
----------------
- Generate SHA-256 hashes
- Hash files
- Hash strings
- Hash bytes
"""

from __future__ import annotations

import hashlib
from pathlib import Path


class Checksum:
    """
    Utility class for generating SHA-256 hashes.
    """

    CHUNK_SIZE = 8192

    @staticmethod
    def from_bytes(data: bytes) -> str:
        """
        Generate SHA-256 hash from bytes.
        """
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def from_text(text: str) -> str:
        """
        Generate SHA-256 hash from text.
        """
        return Checksum.from_bytes(text.encode("utf-8"))

    @staticmethod
    def from_file(path: Path) -> str:
        """
        Generate SHA-256 hash for a file.

        Reads file in chunks to support
        very large SEC filings.
        """

        sha = hashlib.sha256()

        with path.open("rb") as file:
            while chunk := file.read(Checksum.CHUNK_SIZE):
                sha.update(chunk)

        return sha.hexdigest()

    @staticmethod
    def verify(path: Path, expected_hash: str) -> bool:
        """
        Verify file integrity.
        """

        return Checksum.from_file(path) == expected_hash