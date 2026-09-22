from __future__ import annotations
import hashlib
from pathlib import Path
class Checksum:
    CHUNK_SIZE = 8192
    @staticmethod
    def from_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()
    @staticmethod
    def from_text(text: str) -> str:
        return Checksum.from_bytes(text.encode("utf-8"))
    @staticmethod
    def from_file(path: Path) -> str:
        sha = hashlib.sha256()
        with path.open("rb") as file:
            while chunk := file.read(Checksum.CHUNK_SIZE):
                sha.update(chunk)
        return sha.hexdigest()
    @staticmethod
    def verify(path: Path, expected_hash: str) -> bool:
        return Checksum.from_file(path) == expected_hash