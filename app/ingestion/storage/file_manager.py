"""
file_manager.py

Low-level file operations for AI Financial Analyst.

Responsibilities
----------------
- Read/write JSON
- Read/write text
- Read/write bytes
- Atomic file writes
- Safe directory creation
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any


class FileManager:
    """
    Low-level filesystem operations.

    This class should be the ONLY place where the
    application directly reads or writes files.
    """

    @staticmethod
    def exists(path: Path) -> bool:
        """Return True if file exists."""
        return path.exists()

    @staticmethod
    def delete(path: Path) -> None:
        """Delete file if it exists."""
        if path.exists():
            path.unlink()

    @staticmethod
    def load_text(path: Path) -> str:
        """Read UTF-8 text file."""
        return path.read_text(encoding="utf-8")

    @staticmethod
    def save_text(path: Path, content: str) -> None:
        """
        Save UTF-8 text using atomic write.
        """
        FileManager.atomic_write(
            path,
            content.encode("utf-8"),
        )

    @staticmethod
    def load_bytes(path: Path) -> bytes:
        """Read binary file."""
        return path.read_bytes()

    @staticmethod
    def save_bytes(path: Path, content: bytes) -> None:
        """Save binary file."""
        FileManager.atomic_write(path, content)

    @staticmethod
    def load_json(path: Path) -> dict[str, Any]:
        """Read JSON file."""
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    @staticmethod
    def save_json(
        path: Path,
        data: dict[str, Any],
    ) -> None:
        """
        Save JSON using atomic write.
        """

        json_bytes = json.dumps(
            data,
            indent=4,
            ensure_ascii=False,
        ).encode("utf-8")

        FileManager.atomic_write(
            path,
            json_bytes,
        )

    @staticmethod
    def atomic_write(
        path: Path,
        content: bytes,
    ) -> None:
        """
        Atomically write a file.

        Prevents partially written files if the
        application crashes during writing.
        """

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with tempfile.NamedTemporaryFile(
            delete=False,
            dir=path.parent,
        ) as tmp:

            tmp.write(content)

            temp_path = Path(tmp.name)

        temp_path.replace(path)