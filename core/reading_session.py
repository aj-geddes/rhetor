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

    def reset(self) -> ReadingChunk | None:
        """Reset to the beginning of the document."""
        self._position = 0
        return self.current_chunk
