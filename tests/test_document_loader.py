"""Tests for the unified document loader."""

from pathlib import Path

import pytest

from core.document_loader import load_document
from core.parsers import FileAccessError, UnsupportedFormatError


class TestDocumentLoader:
    def test_load_txt(self, txt_simple: Path) -> None:
        doc = load_document(txt_simple)
        assert doc.metadata.format == ".txt"
        assert doc.word_count > 0

    def test_load_md(self, md_full: Path) -> None:
        doc = load_document(md_full)
        assert doc.metadata.format == ".md"
        assert doc.word_count > 0

    def test_load_docx(self, docx_simple: Path) -> None:
        doc = load_document(docx_simple)
        assert doc.metadata.format == ".docx"
        assert doc.word_count > 0

    def test_load_pdf(self, pdf_simple: Path) -> None:
        doc = load_document(pdf_simple)
        assert doc.metadata.format == ".pdf"
        assert doc.word_count > 0

    def test_unsupported_format(self, tmp_path: Path) -> None:
        p = tmp_path / "file.xyz"
        p.write_text("content")
        with pytest.raises(UnsupportedFormatError, match="Unsupported format"):
            load_document(p)

    def test_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileAccessError):
            load_document(tmp_path / "does_not_exist.txt")

    def test_string_path_accepted(self, txt_simple: Path) -> None:
        doc = load_document(str(txt_simple))
        assert doc.metadata.format == ".txt"
