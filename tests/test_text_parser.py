"""Tests for the plain text parser."""

from pathlib import Path

import pytest

from core.models import ElementType
from core.parsers import FileAccessError
from core.parsers.text_parser import TextParser


@pytest.fixture
def parser() -> TextParser:
    return TextParser()


class TestTextParser:
    def test_simple_parsing(self, parser: TextParser, txt_simple: Path) -> None:
        doc = parser.parse(txt_simple)
        assert len(doc.elements) == 3
        assert all(el.element_type == ElementType.PARAGRAPH for el in doc.elements)
        assert "paragraph one" in doc.elements[0].content
        assert "paragraph two" in doc.elements[1].content

    def test_unicode(self, parser: TextParser, txt_unicode: Path) -> None:
        doc = parser.parse(txt_unicode)
        assert "\u00e9" in doc.full_text  # é
        assert "\u3053\u3093\u306b\u3061\u306f" in doc.full_text  # こんにちは

    def test_latin1_encoding(self, parser: TextParser, txt_latin1: Path) -> None:
        doc = parser.parse(txt_latin1)
        assert "Caf" in doc.full_text
        assert len(doc.elements) >= 1

    def test_empty_file(self, parser: TextParser, txt_empty: Path) -> None:
        doc = parser.parse(txt_empty)
        assert len(doc.elements) == 0
        assert doc.word_count == 0

    def test_crlf_normalization(self, parser: TextParser, txt_crlf: Path) -> None:
        doc = parser.parse(txt_crlf)
        assert len(doc.elements) == 2
        assert "Line one." in doc.elements[0].content
        assert "Line two." in doc.elements[1].content

    def test_missing_file(self, parser: TextParser, tmp_path: Path) -> None:
        with pytest.raises(FileAccessError):
            parser.parse(tmp_path / "nonexistent.txt")

    def test_metadata(self, parser: TextParser, txt_simple: Path) -> None:
        doc = parser.parse(txt_simple)
        assert doc.metadata.format == ".txt"
        assert doc.metadata.title == "simple"
        assert doc.metadata.file_size_bytes > 0
