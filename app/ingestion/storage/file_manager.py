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
        # missing_ok guards the exists()/unlink() race on Windows where the
        # file can disappear between the check and the unlink call.
        path.unlink(missing_ok=True)

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
        # On Windows a concurrent unlink can surface as PermissionError when
        # the file is opened between exists() and open(). Propagate the same
        # FileNotFoundError callers already handle so races are not 500s.
        try:
            with path.open(
                "r",
                encoding="utf-8",
            ) as file:
                return json.load(file)
        except PermissionError:
            if not path.exists():
                raise FileNotFoundError(str(path)) from None
            raise
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