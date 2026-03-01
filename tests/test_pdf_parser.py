"""Tests for the PDF parser."""

from pathlib import Path

import pytest

from core.parsers import FileAccessError
from core.parsers.pdf_parser import PdfParser


@pytest.fixture
def parser() -> PdfParser:
    return PdfParser()


class TestPdfParser:
    def test_simple_extraction(self, parser: PdfParser, pdf_simple: Path) -> None:
        doc = parser.parse(pdf_simple)
        assert len(doc.elements) >= 1
        full = doc.full_text
        assert "first paragraph" in full.lower() or "Simple PDF" in full

    def test_multipage(self, parser: PdfParser, pdf_multipage: Path) -> None:
        doc = parser.parse(pdf_multipage)
        full = doc.full_text
        assert "Page 1" in full
        assert "Page 2" in full
        assert "Page 3" in full

    def test_empty_page_handled(self, parser: PdfParser, pdf_empty_page: Path) -> None:
        doc = parser.parse(pdf_empty_page)
        assert len(doc.elements) >= 1
        full = doc.full_text
        assert "Page two has text" in full

    def test_metadata_extraction(self, parser: PdfParser, pdf_with_metadata: Path) -> None:
        doc = parser.parse(pdf_with_metadata)
        assert doc.metadata.title == "My PDF Title"
        assert doc.metadata.author == "Jane Doe"
        assert doc.metadata.format == ".pdf"

    def test_page_count(self, parser: PdfParser, pdf_multipage: Path) -> None:
        doc = parser.parse(pdf_multipage)
        assert doc.metadata.page_count == 3

    def test_missing_file(self, parser: PdfParser, tmp_path: Path) -> None:
        with pytest.raises(FileAccessError):
            parser.parse(tmp_path / "nonexistent.pdf")

    def test_word_count(self, parser: PdfParser, pdf_simple: Path) -> None:
        doc = parser.parse(pdf_simple)
        assert doc.word_count > 0
