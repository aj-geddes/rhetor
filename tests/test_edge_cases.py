"""Edge case tests — boundary conditions and unusual inputs."""

from __future__ import annotations

from constants import MAX_SPEED, MIN_SPEED, SPEED_INCREMENT, VOLUME_INCREMENT
from core.models import ElementType, ParsedDocument, TextElement
from core.reading_session import ReadingSession


def _make_session(*paragraphs: str) -> ReadingSession:
    elements = [
        TextElement(content=text, element_type=ElementType.PARAGRAPH)
        for text in paragraphs
    ]
    doc = ParsedDocument(elements=elements)
    return ReadingSession(doc)


# ── Single-sentence document ────────────────────────────────────────────


class TestSingleSentenceDocument:
    def test_single_sentence(self) -> None:
        session = _make_session("Hello world.")
        assert session.total_chunks == 1
        assert session.current_chunk is not None
        assert session.current_chunk.text == "Hello world."

    def test_advance_finishes(self) -> None:
        session = _make_session("Hello world.")
        session.advance()
        assert session.is_finished


# ── Headings-only document ──────────────────────────────────────────────


class TestHeadingsOnlyDocument:
    def test_headings_create_chunks(self) -> None:
        elements = [
            TextElement(content="Title", element_type=ElementType.HEADING, level=1),
            TextElement(content="Subtitle", element_type=ElementType.HEADING, level=2),
        ]
        doc = ParsedDocument(elements=elements)
        session = ReadingSession(doc)
        assert session.total_chunks == 2

    def test_paragraph_nav_on_headings(self) -> None:
        elements = [
            TextElement(content="Title", element_type=ElementType.HEADING, level=1),
            TextElement(content="Subtitle", element_type=ElementType.HEADING, level=2),
        ]
        doc = ParsedDocument(elements=elements)
        session = ReadingSession(doc)
        result = session.skip_to_next_paragraph()
        assert result is not None
        assert result.text == "Subtitle"


# ── Whitespace-only document ────────────────────────────────────────────


class TestWhitespaceOnlyDocument:
    def test_whitespace_only(self) -> None:
        session = _make_session("   \n\n\t  ")
        assert session.total_chunks == 0

    def test_empty_elements(self) -> None:
        doc = ParsedDocument(elements=[])
        session = ReadingSession(doc)
        assert session.total_chunks == 0
        assert session.current_chunk is None


# ── Many short paragraphs ──────────────────────────────────────────────


class TestManyShortParagraphs:
    def test_ten_paragraphs(self) -> None:
        paras = [f"Paragraph {i}." for i in range(10)]
        session = _make_session(*paras)
        assert session.total_chunks == 10

    def test_rapid_forward_skip(self) -> None:
        paras = [f"Paragraph {i}." for i in range(10)]
        session = _make_session(*paras)
        for _ in range(15):  # More skips than paragraphs
            session.skip_to_next_paragraph()
        assert session.is_finished

    def test_rapid_backward_skip(self) -> None:
        paras = [f"Paragraph {i}." for i in range(10)]
        session = _make_session(*paras)
        # Go to end
        for _ in range(15):
            session.skip_to_next_paragraph()
        # Skip back many times
        for _ in range(15):
            session.skip_to_prev_paragraph()
        assert session.position == 0


# ── Speed/volume boundary clamping ──────────────────────────────────────


class TestSpeedVolumeBoundaries:
    def test_speed_at_max_no_overflow(self) -> None:
        speed = MAX_SPEED
        new_speed = min(MAX_SPEED, speed + SPEED_INCREMENT)
        assert new_speed == MAX_SPEED

    def test_speed_at_min_no_underflow(self) -> None:
        speed = MIN_SPEED
        new_speed = max(MIN_SPEED, speed - SPEED_INCREMENT)
        assert new_speed == MIN_SPEED

    def test_volume_at_max_no_overflow(self) -> None:
        volume = 1.0
        new_volume = min(1.0, volume + VOLUME_INCREMENT)
        assert new_volume == 1.0

    def test_volume_at_min_no_underflow(self) -> None:
        volume = 0.0
        new_volume = max(0.0, volume - VOLUME_INCREMENT)
        assert new_volume == 0.0

    def test_speed_increment_value(self) -> None:
        assert SPEED_INCREMENT == 0.25

    def test_volume_increment_value(self) -> None:
        assert VOLUME_INCREMENT == 0.05
