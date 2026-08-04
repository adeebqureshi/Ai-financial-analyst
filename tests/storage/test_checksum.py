from pathlib import Path

from app.ingestion.storage.checksum import Checksum


def test_text_hash():

    hash1 = Checksum.from_text("Apple")

    hash2 = Checksum.from_text("Apple")

    assert hash1 == hash2


def test_text_hash_difference():

    hash1 = Checksum.from_text("Apple")

    hash2 = Checksum.from_text("Microsoft")

    assert hash1 != hash2


def test_file_hash(tmp_path: Path):

    file = tmp_path / "sample.txt"

    file.write_text("AI Financial Analyst")

    digest = Checksum.from_file(file)

    assert isinstance(digest, str)

    assert len(digest) == 64


def test_verify(tmp_path: Path):

    file = tmp_path / "sample.txt"

    file.write_text("OpenAI")

    digest = Checksum.from_file(file)

    assert Checksum.verify(file, digest)