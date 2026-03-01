"""Text processor — sentence segmentation, chunking, and duration estimation."""

from __future__ import annotations

import re

from constants import DEFAULT_WORDS_PER_MINUTE
from core.models import ChunkType, ElementType, ParsedDocument, ReadingChunk

# ── Sentence segmentation ────────────────────────────────────────────────────

# Common abbreviations that use periods but don't end sentences
_ABBREVIATIONS = frozenset({
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "ave", "blvd",
    "dept", "est", "vol", "vs", "etc", "inc", "ltd", "corp", "govt",
    "gen", "sgt", "cpl", "pvt", "capt", "lt", "col", "maj", "cmdr",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct",
    "nov", "dec", "mon", "tue", "wed", "thu", "fri", "sat", "sun",
    "fig", "eq", "ref", "no", "nos",
})

# Pattern for initials like U.S., A.M., P.M., e.g., i.e.
_INITIALS_PATTERN = re.compile(r"^[A-Za-z](\.[A-Za-z])+\.?$")

# Protect abbreviations by replacing their periods with a placeholder
_ABBREV_PLACEHOLDER = "\x01"

# Sentence-ending punctuation followed by whitespace/end
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"\u2018\u201C(])")


def _element_to_chunk_type(element_type: ElementType) -> ChunkType:
    """Map document element types to chunk types."""
    mapping = {
        ElementType.HEADING: ChunkType.HEADING,
        ElementType.TABLE: ChunkType.TABLE_ROW,
        ElementType.CODE_BLOCK: ChunkType.CODE_BLOCK,
        ElementType.LIST_ITEM: ChunkType.LIST_ITEM,
        ElementType.BLOCKQUOTE: ChunkType.BLOCKQUOTE,
    }
    return mapping.get(element_type, ChunkType.SENTENCE)


class TextProcessor:
    """Process a ParsedDocument into ReadingChunks for TTS consumption."""

    def __init__(self, words_per_minute: int = DEFAULT_WORDS_PER_MINUTE) -> None:
        self._wpm = words_per_minute

    def process(self, document: ParsedDocument) -> list[ReadingChunk]:
        """Convert a parsed document into an ordered list of ReadingChunks."""
        chunks: list[ReadingChunk] = []
        char_offset = 0

        for para_idx, element in enumerate(document.elements):
            content = self._normalize_whitespace(element.content)
            if not content:
                continue

            chunk_type = _element_to_chunk_type(element.element_type)

            # For headings, code blocks, table rows — don't split into sentences
            if chunk_type != ChunkType.SENTENCE:
                chunk = ReadingChunk(
                    text=content,
                    paragraph_index=para_idx,
                    sentence_index=0,
                    char_offset_start=char_offset,
                    char_offset_end=char_offset + len(content),
                    chunk_type=chunk_type,
                )
                chunks.append(chunk)
                char_offset += len(content) + 2  # +2 for paragraph separator
                continue

            # Sentence segmentation for regular paragraphs
            sentences = self._segment_sentences(content)
            sent_offset = char_offset
            for sent_idx, sentence in enumerate(sentences):
                chunk = ReadingChunk(
                    text=sentence,
                    paragraph_index=para_idx,
                    sentence_index=sent_idx,
                    char_offset_start=sent_offset,
                    char_offset_end=sent_offset + len(sentence),
                    chunk_type=ChunkType.SENTENCE,
                )
                chunks.append(chunk)
                sent_offset += len(sentence) + 1  # +1 for space between sentences

            char_offset += len(content) + 2

        return chunks

    def estimate_duration_seconds(self, chunks: list[ReadingChunk]) -> float:
        """Estimate total reading duration based on word count and WPM."""
        total_words = sum(len(c.text.split()) for c in chunks)
        return (total_words / self._wpm) * 60

    def _normalize_whitespace(self, text: str) -> str:
        """Collapse runs of whitespace into single spaces."""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Collapse multiple spaces (but preserve single newlines for paragraph structure)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n", "\n\n", text)
        return text.strip()

    def _segment_sentences(self, text: str) -> list[str]:
        """Split text into sentences using a protection-then-split approach.

        Protects abbreviations and decimals from false splits, then splits
        on sentence-ending punctuation followed by whitespace + uppercase.
        """
        # Protect decimal numbers (e.g., 3.14, $12.50)
        protected = re.sub(
            r"(\d)\.(\d)",
            rf"\1{_ABBREV_PLACEHOLDER}\2",
            text,
        )

        # Protect abbreviations (e.g., Mr., Dr., U.S.)
        words = protected.split()
        rebuilt = []
        for word in words:
            lower_base = word.rstrip(".,;:!?\"')").lower().rstrip(".")
            if lower_base in _ABBREVIATIONS or _INITIALS_PATTERN.match(word.rstrip(".,;:!?\"')")):
                rebuilt.append(word.replace(".", _ABBREV_PLACEHOLDER))
            else:
                rebuilt.append(word)
        protected = " ".join(rebuilt)

        # Split on sentence boundaries
        raw_sentences = _SENTENCE_SPLIT.split(protected)

        # Restore placeholders
        sentences = [
            s.replace(_ABBREV_PLACEHOLDER, ".").strip()
            for s in raw_sentences
            if s.strip()
        ]

        return sentences
