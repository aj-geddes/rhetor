"""Tests for paragraph navigation in ReadingSession."""

from __future__ import annotations

from core.models import ElementType, ParsedDocument, TextElement
from core.reading_session import ReadingSession


def _make_session(*paragraphs: str) -> ReadingSession:
    """Create a ReadingSession with one element per paragraph."""
    elements = [
        TextElement(content=text, element_type=ElementType.PARAGRAPH)
        for text in paragraphs
    ]
    doc = ParsedDocument(elements=elements)
    return ReadingSession(doc)


# ── skip_to_next_paragraph ───────────────────────────────────────────────


class TestSkipToNextParagraph:
    def test_moves_to_next_paragraph(self) -> None:
        session = _make_session(
            "First sentence. Second sentence.",
            "Third sentence.",
        )
        assert session.position == 0
        result = session.skip_to_next_paragraph()
        assert result is not None
        assert result.paragraph_index == 1

    def test_skips_remaining_sentences_in_paragraph(self) -> None:
        session = _make_session(
            "First. Second. Third.",
            "Fourth.",
        )
        # Position at first chunk (sentence 0 of paragraph 0)
        assert session.position == 0
        result = session.skip_to_next_paragraph()
        assert result is not None
        assert result.paragraph_index == 1

    def test_from_middle_of_paragraph(self) -> None:
        session = _make_session(
            "First sentence. Second sentence. Third sentence.",
            "Fourth sentence.",
        )
        session.advance()  # move to sentence 1 of paragraph 0
        result = session.skip_to_next_paragraph()
        assert result is not None
        assert result.paragraph_index == 1

    def test_returns_none_at_last_paragraph(self) -> None:
        session = _make_session("Only paragraph.")
        result = session.skip_to_next_paragraph()
        assert result is None
        assert session.is_finished

    def test_returns_none_when_already_finished(self) -> None:
        session = _make_session("Only paragraph.")
        session._position = len(session.chunks)  # past end
        result = session.skip_to_next_paragraph()
        assert result is None

    def test_three_paragraphs_step_through(self) -> None:
        session = _make_session("Para one.", "Para two.", "Para three.")
        r1 = session.skip_to_next_paragraph()
        assert r1 is not None
        assert r1.paragraph_index == 1
        r2 = session.skip_to_next_paragraph()
        assert r2 is not None
        assert r2.paragraph_index == 2
        r3 = session.skip_to_next_paragraph()
        assert r3 is None
        assert session.is_finished

    def test_empty_document(self) -> None:
        doc = ParsedDocument(elements=[])
        session = ReadingSession(doc)
        result = session.skip_to_next_paragraph()
        assert result is None


# ── skip_to_prev_paragraph ───────────────────────────────────────────────


class TestSkipToPrevParagraph:
    def test_goes_to_start_of_current_paragraph(self) -> None:
        session = _make_session(
            "First sentence. Second sentence. Third sentence.",
            "Fourth sentence.",
        )
        session.advance()  # move to sentence 1
        session.advance()  # move to sentence 2
        result = session.skip_to_prev_paragraph()
        assert result is not None
        assert result.paragraph_index == 0
        assert result.sentence_index == 0

    def test_at_start_of_paragraph_goes_to_previous(self) -> None:
        session = _make_session(
            "First sentence.",
            "Second sentence. Third sentence.",
        )
        session.skip_to_next_paragraph()  # move to paragraph 1
        result = session.skip_to_prev_paragraph()
        assert result is not None
        assert result.paragraph_index == 0

    def test_at_start_of_first_paragraph_stays(self) -> None:
        session = _make_session("Only paragraph.")
        result = session.skip_to_prev_paragraph()
        assert result is not None
        assert session.position == 0

    def test_clamps_at_zero(self) -> None:
        session = _make_session("First.", "Second.")
        # At start of first paragraph
        result = session.skip_to_prev_paragraph()
        assert result is not None
        assert session.position == 0

    def test_three_paragraphs_backward(self) -> None:
        session = _make_session("Para one.", "Para two.", "Para three.")
        # Go to last paragraph
        session.skip_to_next_paragraph()
        session.skip_to_next_paragraph()
        assert session.current_chunk is not None
        assert session.current_chunk.paragraph_index == 2

        r1 = session.skip_to_prev_paragraph()
        assert r1 is not None
        assert r1.paragraph_index == 1

        r2 = session.skip_to_prev_paragraph()
        assert r2 is not None
        assert r2.paragraph_index == 0

    def test_empty_document(self) -> None:
        doc = ParsedDocument(elements=[])
        session = ReadingSession(doc)
        result = session.skip_to_prev_paragraph()
        assert result is None

    def test_from_past_end_goes_to_last_paragraph(self) -> None:
        session = _make_session("First.", "Second.")
        session._position = len(session.chunks)  # past end
        result = session.skip_to_prev_paragraph()
        assert result is not None
        # Should go to start of last paragraph
        assert result.paragraph_index == 1
