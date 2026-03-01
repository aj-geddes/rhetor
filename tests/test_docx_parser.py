"""Tests for the DOCX parser."""

from pathlib import Path

import pytest

from core.models import ElementType
from core.parsers import FileAccessError
from core.parsers.docx_parser import DocxParser


@pytest.fixture
def parser() -> DocxParser:
    return DocxParser()


class TestDocxParser:
    def test_headings_detected(self, parser: DocxParser, docx_simple: Path) -> None:
        doc = parser.parse(docx_simple)
        headings = [el for el in doc.elements if el.element_type == ElementType.HEADING]
        assert len(headings) >= 2
        assert headings[0].content == "Document Title"
        assert headings[0].level == 1
        assert headings[1].content == "Section Two"
        assert headings[1].level == 2

    def test_paragraphs(self, parser: DocxParser, docx_simple: Path) -> None:
        doc = parser.parse(docx_simple)
        paragraphs = [el for el in doc.elements if el.element_type == ElementType.PARAGRAPH]
        assert len(paragraphs) >= 2
        assert "First paragraph" in paragraphs[0].content

    def test_table_extraction(self, parser: DocxParser, docx_with_table: Path) -> None:
        doc = parser.parse(docx_with_table)
        tables = [el for el in doc.elements if el.element_type == ElementType.TABLE]
        assert len(tables) >= 2  # 2 rows
        assert "A1" in tables[0].content
        assert "B1" in tables[0].content

    def test_metadata(self, parser: DocxParser, docx_simple: Path) -> None:
        doc = parser.parse(docx_simple)
        assert doc.metadata.title == "Test Document"
        assert doc.metadata.author == "Test Author"
        assert doc.metadata.format == ".docx"

    def test_empty_document(self, parser: DocxParser, docx_empty: Path) -> None:
        doc = parser.parse(docx_empty)
        assert len(doc.elements) == 0

    def test_missing_file(self, parser: DocxParser, tmp_path: Path) -> None:
        with pytest.raises(FileAccessError):
            parser.parse(tmp_path / "nonexistent.docx")

    def test_word_count(self, parser: DocxParser, docx_simple: Path) -> None:
        doc = parser.parse(docx_simple)
        assert doc.word_count > 0
