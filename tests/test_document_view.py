"""Tests for ui/document_view.py — welcome screen, display, highlighting."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest

from core.models import (
    ChunkType,
    DocumentMetadata,
    ElementType,
    ParsedDocument,
    ReadingChunk,
    TextElement,
)


@pytest.fixture
def root() -> Generator[Any, None, None]:
    """Create a tkinter root window for testing, skip if no display."""
    try:
        import customtkinter as ctk

        root = ctk.CTk()
        root.withdraw()
        yield root
        root.destroy()
    except Exception:
        pytest.skip("No display available for UI tests")


@pytest.fixture
def doc_view(root: Any) -> Any:
    from ui.document_view import DocumentView

    view = DocumentView(root)
    view.pack()
    return view


def _make_document(text: str = "Hello world. This is a test.") -> ParsedDocument:
    """Create a simple ParsedDocument for testing."""
    return ParsedDocument(
        elements=[TextElement(content=text, element_type=ElementType.PARAGRAPH)],
        metadata=DocumentMetadata(title="Test", format="txt"),
    )


class TestDocumentViewWidget:
    def test_welcome_screen_shown_initially(self, doc_view) -> None:  # type: ignore[no-untyped-def]
        content = doc_view._textbox.get("1.0", "end").strip()
        assert "Open a document" in content

    def test_load_document_replaces_welcome(self, doc_view) -> None:  # type: ignore[no-untyped-def]
        doc = _make_document("The quick brown fox.")
        doc_view.load_document(doc)
        content = doc_view._textbox.get("1.0", "end").strip()
        assert "The quick brown fox." in content
        assert "Open a document" not in content

    def test_highlight_chunk(self, doc_view) -> None:  # type: ignore[no-untyped-def]
        doc = _make_document("Hello world. This is a test.")
        doc_view.load_document(doc)

        chunk = ReadingChunk(
            text="Hello world.",
            paragraph_index=0,
            sentence_index=0,
            char_offset_start=0,
            char_offset_end=12,
            chunk_type=ChunkType.SENTENCE,
        )
        doc_view.highlight_chunk(chunk)

        # Verify tag was applied
        ranges = doc_view._textbox._textbox.tag_ranges("current_chunk")
        assert len(ranges) == 2  # start, end pair

    def test_clear_highlight(self, doc_view) -> None:  # type: ignore[no-untyped-def]
        doc = _make_document("Hello world.")
        doc_view.load_document(doc)

        chunk = ReadingChunk(
            text="Hello world.",
            paragraph_index=0,
            sentence_index=0,
            char_offset_start=0,
            char_offset_end=12,
        )
        doc_view.highlight_chunk(chunk)
        doc_view.clear_highlight()

        ranges = doc_view._textbox._textbox.tag_ranges("current_chunk")
        assert len(ranges) == 0

    def test_set_font_size(self, doc_view) -> None:  # type: ignore[no-untyped-def]
        doc_view.set_font_size(18)
        assert doc_view._font_size == 18

    def test_show_welcome_after_document(self, doc_view) -> None:  # type: ignore[no-untyped-def]
        doc = _make_document("Some text.")
        doc_view.load_document(doc)
        doc_view.show_welcome()
        content = doc_view._textbox.get("1.0", "end").strip()
        assert "Open a document" in content

    def test_welcome_mentions_f1(self, doc_view) -> None:  # type: ignore[no-untyped-def]
        content = doc_view._textbox.get("1.0", "end").strip()
        assert "F1" in content

    def test_show_empty_document_message(self, doc_view) -> None:  # type: ignore[no-untyped-def]
        doc_view.show_empty_document_message("/tmp/test.pdf")
        content = doc_view._textbox.get("1.0", "end").strip()
        assert "No readable text" in content
        assert "test.pdf" in content
