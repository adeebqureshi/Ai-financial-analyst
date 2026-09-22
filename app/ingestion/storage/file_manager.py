from __future__ import annotations
import json
import tempfile
from pathlib import Path
from typing import Any
class FileManager:
    @staticmethod
    def exists(path: Path) -> bool:
        return path.exists()
    @staticmethod
    def delete(path: Path) -> None:
        if path.exists():
            path.unlink()
    @staticmethod
    def load_text(path: Path) -> str:
        return path.read_text(encoding="utf-8")
    @staticmethod
    def save_text(path: Path, content: str) -> None:
        FileManager.atomic_write(
            path,
            content.encode("utf-8"),
        )
    @staticmethod
    def load_bytes(path: Path) -> bytes:
        return path.read_bytes()
    @staticmethod
    def save_bytes(path: Path, content: bytes) -> None:
        FileManager.atomic_write(path, content)
    @staticmethod
    def load_json(path: Path) -> dict[str, Any]:
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