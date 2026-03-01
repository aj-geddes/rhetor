"""Tests for text processor — sentence segmentation, chunking, duration."""

import pytest

from core.models import ChunkType, ElementType, ParsedDocument, TextElement
from core.text_processor import TextProcessor


@pytest.fixture
def processor() -> TextProcessor:
    return TextProcessor()


def _make_doc(texts: list[str], element_type: ElementType = ElementType.PARAGRAPH) -> ParsedDocument:
    """Helper to create a ParsedDocument from a list of text strings."""
    elements = [TextElement(content=t, element_type=element_type) for t in texts]
    return ParsedDocument(elements=elements)


class TestSentenceSegmentation:
    def test_simple_sentences(self, processor: TextProcessor) -> None:
        doc = _make_doc(["First sentence. Second sentence. Third sentence."])
        chunks = processor.process(doc)
        assert len(chunks) == 3
        assert chunks[0].text == "First sentence."
        assert chunks[1].text == "Second sentence."
        assert chunks[2].text == "Third sentence."

    def test_abbreviation_mr(self, processor: TextProcessor) -> None:
        doc = _make_doc(["Mr. Smith went to Washington. He arrived at noon."])
        chunks = processor.process(doc)
        assert len(chunks) == 2
        assert "Mr. Smith" in chunks[0].text

    def test_abbreviation_dr(self, processor: TextProcessor) -> None:
        doc = _make_doc(["Dr. Jones is here. She is a doctor."])
        chunks = processor.process(doc)
        assert len(chunks) == 2
        assert "Dr. Jones" in chunks[0].text

    def test_abbreviation_us(self, processor: TextProcessor) -> None:
        doc = _make_doc(["The U.S. government issued a statement. It was important."])
        chunks = processor.process(doc)
        assert len(chunks) == 2
        assert "U.S." in chunks[0].text

    def test_decimal_numbers(self, processor: TextProcessor) -> None:
        doc = _make_doc(["The value is 3.14 approximately. That is pi."])
        chunks = processor.process(doc)
        assert len(chunks) == 2
        assert "3.14" in chunks[0].text

    def test_multiple_punctuation(self, processor: TextProcessor) -> None:
        doc = _make_doc(["What happened?! Nobody knows. It was chaos."])
        chunks = processor.process(doc)
        assert len(chunks) >= 2

    def test_exclamation(self, processor: TextProcessor) -> None:
        doc = _make_doc(["Hello! How are you?"])
        chunks = processor.process(doc)
        assert len(chunks) == 2
        assert chunks[0].text == "Hello!"
        assert chunks[1].text == "How are you?"

    def test_single_sentence(self, processor: TextProcessor) -> None:
        doc = _make_doc(["Just one sentence here."])
        chunks = processor.process(doc)
        assert len(chunks) == 1


class TestChunkTypes:
    def test_heading_chunk_type(self, processor: TextProcessor) -> None:
        doc = _make_doc(["Chapter One"], ElementType.HEADING)
        chunks = processor.process(doc)
        assert len(chunks) == 1
        assert chunks[0].chunk_type == ChunkType.HEADING

    def test_table_chunk_type(self, processor: TextProcessor) -> None:
        doc = _make_doc(["A | B | C"], ElementType.TABLE)
        chunks = processor.process(doc)
        assert chunks[0].chunk_type == ChunkType.TABLE_ROW

    def test_code_block_chunk_type(self, processor: TextProcessor) -> None:
        doc = _make_doc(["print('hello')"], ElementType.CODE_BLOCK)
        chunks = processor.process(doc)
        assert chunks[0].chunk_type == ChunkType.CODE_BLOCK

    def test_heading_not_split(self, processor: TextProcessor) -> None:
        doc = _make_doc(["This is heading. With two sentences."], ElementType.HEADING)
        chunks = processor.process(doc)
        # Headings should NOT be split into sentences
        assert len(chunks) == 1


class TestChunkOffsets:
    def test_offsets_sequential(self, processor: TextProcessor) -> None:
        doc = _make_doc(["First. Second.", "Third paragraph."])
        chunks = processor.process(doc)
        for i in range(len(chunks) - 1):
            # Each chunk's start should be >= previous chunk's start
            assert chunks[i + 1].char_offset_start >= chunks[i].char_offset_start

    def test_offset_range_matches_text_length(self, processor: TextProcessor) -> None:
        doc = _make_doc(["Hello world."])
        chunks = processor.process(doc)
        for chunk in chunks:
            assert chunk.char_offset_end - chunk.char_offset_start == len(chunk.text)

    def test_paragraph_indices(self, processor: TextProcessor) -> None:
        doc = _make_doc(["Para one.", "Para two.", "Para three."])
        chunks = processor.process(doc)
        assert chunks[0].paragraph_index == 0
        assert chunks[1].paragraph_index == 1
        assert chunks[2].paragraph_index == 2


class TestDurationEstimation:
    def test_estimation_positive(self, processor: TextProcessor) -> None:
        doc = _make_doc(["This is a test sentence with several words in it."])
        chunks = processor.process(doc)
        duration = processor.estimate_duration_seconds(chunks)
        assert duration > 0

    def test_empty_document(self, processor: TextProcessor) -> None:
        doc = _make_doc([])
        chunks = processor.process(doc)
        duration = processor.estimate_duration_seconds(chunks)
        assert duration == 0.0

    def test_custom_wpm(self) -> None:
        fast = TextProcessor(words_per_minute=300)
        slow = TextProcessor(words_per_minute=100)
        doc = _make_doc(["This is a sentence with ten words in it here."])
        fast_chunks = fast.process(doc)
        slow_chunks = slow.process(doc)
        assert fast.estimate_duration_seconds(fast_chunks) < slow.estimate_duration_seconds(
            slow_chunks
        )
