from pathlib import Path

from app.ingestion.storage.file_manager import FileManager


def test_text_file(tmp_path: Path):

    file = tmp_path / "test.txt"

    FileManager.save_text(
        file,
        "hello",
    )

    assert FileManager.exists(file)

    assert FileManager.load_text(file) == "hello"


def test_json_file(tmp_path: Path):

    file = tmp_path / "data.json"

    data = {
        "ticker": "AAPL",
        "year": 2024,
    }

    FileManager.save_json(
        file,
        data,
    )

    loaded = FileManager.load_json(file)

    assert loaded == data


def test_binary_file(tmp_path: Path):

    file = tmp_path / "sample.bin"

    FileManager.save_bytes(
        file,
        b"ABC",
    )

    assert FileManager.load_bytes(file) == b"ABC"


def test_delete(tmp_path: Path):

    file = tmp_path / "remove.txt"

    FileManager.save_text(
        file,
        "delete me",
    )

    assert FileManager.exists(file)

    FileManager.delete(file)

    assert not FileManager.exists(file)