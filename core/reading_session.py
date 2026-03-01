"""Reading session — manages loaded document state and chunk navigation."""

from __future__ import annotations

from core.models import ParsedDocument, ReadingChunk
from core.text_processor import TextProcessor


class ReadingSession:
    """Manages the current document, reading position, and navigation."""

    def __init__(
        self,
        document: ParsedDocument,
        processor: TextProcessor | None = None,
    ) -> None:
        self._document = document
        self._processor = processor or TextProcessor()
        self._chunks = self._processor.process(document)
        self._position = 0
        self._estimated_duration = self._processor.estimate_duration_seconds(self._chunks)

    @property
    def document(self) -> ParsedDocument:
        return self._document

    @property
    def chunks(self) -> list[ReadingChunk]:
        return self._chunks

    @property
    def total_chunks(self) -> int:
        return len(self._chunks)

    @property
    def position(self) -> int:
        return self._position

    @property
    def current_chunk(self) -> ReadingChunk | None:
        """Return the chunk at the current position, or None if exhausted."""
        if 0 <= self._position < len(self._chunks):
            return self._chunks[self._position]
        return None

    @property
    def is_finished(self) -> bool:
        return self._position >= len(self._chunks)

    @property
    def estimated_duration(self) -> float:
        """Total estimated reading duration in seconds."""
        return self._estimated_duration

    def advance(self) -> ReadingChunk | None:
        """Move to the next chunk and return it. Returns None when finished."""
        self._position += 1
        return self.current_chunk

    def go_back(self) -> ReadingChunk | None:
        """Move to the previous chunk and return it. Clamps at 0."""
        self._position = max(0, self._position - 1)
        return self.current_chunk

    def jump_to(self, position: int) -> ReadingChunk | None:
        """Jump to a specific chunk position."""
        self._position = max(0, min(position, len(self._chunks) - 1))
        return self.current_chunk

    def skip_to_next_paragraph(self) -> ReadingChunk | None:
        """Skip forward to the first chunk of the next paragraph.

        Returns the chunk at the new position, or None if already in the last
        paragraph (position is set past the end).
        """
        if not self._chunks or self._position >= len(self._chunks):
            return None

        current_para = self._chunks[self._position].paragraph_index
        for i in range(self._position + 1, len(self._chunks)):
            if self._chunks[i].paragraph_index != current_para:
                self._position = i
                return self._chunks[i]

        # Already in the last paragraph — set position past end
        self._position = len(self._chunks)
        return None

    def skip_to_prev_paragraph(self) -> ReadingChunk | None:
        """Skip backward to the start of the current or previous paragraph.

        If not at the first chunk of the current paragraph, moves to the start
        of the current paragraph.  If already at the start, moves to the start
        of the previous paragraph.  Clamps at 0.
        """
        if not self._chunks:
            return None

        was_past_end = self._position >= len(self._chunks)
        self._position = min(self._position, len(self._chunks) - 1)
        current_para = self._chunks[self._position].paragraph_index

        # Find the start of the current paragraph
        para_start = self._position
        while para_start > 0 and self._chunks[para_start - 1].paragraph_index == current_para:
            para_start -= 1

        if was_past_end or self._position > para_start:
            # Not at the start of the current paragraph — go to its start
            self._position = para_start
        else:
            # Already at the start — go to the start of the previous paragraph
            if para_start == 0:
                self._position = 0
            else:
                prev_para = self._chunks[para_start - 1].paragraph_index
                prev_start = para_start - 1
                while (
                    prev_start > 0
                    and self._chunks[prev_start - 1].paragraph_index == prev_para
                ):
                    prev_start -= 1
                self._position = prev_start

        return self.current_chunk

    def reset(self) -> ReadingChunk | None:
        """Reset to the beginning of the document."""
        self._position = 0
        return self.current_chunk
