"""Shared data models for Rhetor's core processing pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class ChunkType(Enum):
    """Classification of a reading chunk for TTS behavior."""

    SENTENCE = auto()
    HEADING = auto()
    TABLE_ROW = auto()
    CODE_BLOCK = auto()
    LIST_ITEM = auto()
    BLOCKQUOTE = auto()


class ElementType(Enum):
    """Classification of a structural element in a parsed document."""

    PARAGRAPH = auto()
    HEADING = auto()
    TABLE = auto()
    CODE_BLOCK = auto()
    LIST_ITEM = auto()
    BLOCKQUOTE = auto()
    HORIZONTAL_RULE = auto()


@dataclass(frozen=True, slots=True)
class ReadingChunk:
    """An immutable unit of text to be spoken by TTS.

    Frozen for thread safety — chunks are produced by the text processor
    and consumed by the TTS worker on a different thread.
    """

    text: str
    paragraph_index: int
    sentence_index: int
    char_offset_start: int
    char_offset_end: int
    chunk_type: ChunkType = ChunkType.SENTENCE


@dataclass(slots=True)
class TextElement:
    """A structural element extracted from a document by a parser."""

    content: str
    element_type: ElementType = ElementType.PARAGRAPH
    level: int = 0  # heading level (1-6) or list nesting depth
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class DocumentMetadata:
    """Metadata extracted from a document."""

    title: str = ""
    author: str = ""
    page_count: int = 0
    format: str = ""
    file_path: str = ""
    file_size_bytes: int = 0


@dataclass(slots=True)
class ParsedDocument:
    """The result of parsing a document — elements + metadata.

    The full_text and word_count are computed automatically from elements.
    """

    elements: list[TextElement]
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata)
    full_text: str = field(init=False, default="")
    word_count: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        self.full_text = "\n\n".join(el.content for el in self.elements if el.content.strip())
        self.word_count = len(self.full_text.split())
