"""Tests for core data models."""

from core.models import (
    ChunkType,
    DocumentMetadata,
    ElementType,
    ParsedDocument,
    ReadingChunk,
    TextElement,
)


class TestChunkType:
    def test_all_variants_exist(self) -> None:
        assert ChunkType.SENTENCE
        assert ChunkType.HEADING
        assert ChunkType.TABLE_ROW
        assert ChunkType.CODE_BLOCK
        assert ChunkType.LIST_ITEM
        assert ChunkType.BLOCKQUOTE


class TestElementType:
    def test_all_variants_exist(self) -> None:
        assert ElementType.PARAGRAPH
        assert ElementType.HEADING
        assert ElementType.TABLE
        assert ElementType.CODE_BLOCK
        assert ElementType.LIST_ITEM
        assert ElementType.BLOCKQUOTE
        assert ElementType.HORIZONTAL_RULE


class TestReadingChunk:
    def test_creation(self) -> None:
        chunk = ReadingChunk(
            text="Hello world.",
            paragraph_index=0,
            sentence_index=0,
            char_offset_start=0,
            char_offset_end=12,
        )
        assert chunk.text == "Hello world."
        assert chunk.chunk_type == ChunkType.SENTENCE

    def test_frozen(self) -> None:
        chunk = ReadingChunk(
            text="Test.", paragraph_index=0, sentence_index=0,
            char_offset_start=0, char_offset_end=5,
        )
        import pytest

        with pytest.raises(AttributeError):
            chunk.text = "Modified"  # type: ignore[misc]

    def test_slots(self) -> None:
        chunk = ReadingChunk(
            text="Test.", paragraph_index=0, sentence_index=0,
            char_offset_start=0, char_offset_end=5,
        )
        assert hasattr(chunk, "__slots__")


class TestTextElement:
    def test_defaults(self) -> None:
        el = TextElement(content="Hello")
        assert el.element_type == ElementType.PARAGRAPH
        assert el.level == 0
        assert el.metadata == {}


class TestDocumentMetadata:
    def test_defaults(self) -> None:
        meta = DocumentMetadata()
        assert meta.title == ""
        assert meta.page_count == 0


class TestParsedDocument:
    def test_full_text_computed(self) -> None:
        doc = ParsedDocument(
            elements=[
                TextElement(content="First paragraph."),
                TextElement(content="Second paragraph."),
            ]
        )
        assert "First paragraph." in doc.full_text
        assert "Second paragraph." in doc.full_text

    def test_word_count_computed(self) -> None:
        doc = ParsedDocument(
            elements=[TextElement(content="one two three four five")]
        )
        assert doc.word_count == 5

    def test_empty_elements_skipped(self) -> None:
        doc = ParsedDocument(
            elements=[
                TextElement(content="Hello."),
                TextElement(content="   "),
                TextElement(content="World."),
            ]
        )
        assert "Hello." in doc.full_text
        assert "World." in doc.full_text
        # The whitespace-only element should be skipped
        assert doc.full_text.count("\n\n") == 1
