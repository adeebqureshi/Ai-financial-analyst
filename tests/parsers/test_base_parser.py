from pathlib import Path

from app.parsers.base_parser import BaseParser


class DummyParser(BaseParser):

    def parse_file(self, file_path: Path) -> str:
        return "parsed"

    def parse_text(self, text: str) -> str:
        return text.upper()


def test_parse_file():

    parser = DummyParser()

    assert parser.parse_file(Path("dummy.html")) == "parsed"


def test_parse_text():

    parser = DummyParser()

    assert parser.parse_text("apple") == "APPLE"