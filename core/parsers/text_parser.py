"""Plain text parser with encoding detection."""

from __future__ import annotations

import re
from pathlib import Path

from charset_normalizer import from_bytes

from core.models import DocumentMetadata, ElementType, ParsedDocument, TextElement
from core.parsers import FileAccessError


class TextParser:
    """Parse .txt files with automatic encoding detection."""

    def parse(self, file_path: Path) -> ParsedDocument:
        if not file_path.exists():
            raise FileAccessError(f"File not found: {file_path}")

        try:
            raw = file_path.read_bytes()
        except OSError as exc:
            raise FileAccessError(f"Cannot read file: {exc}") from exc

        text = self._decode(raw)
        text = self._normalize_line_endings(text)
        elements = self._split_paragraphs(text)

        metadata = DocumentMetadata(
            title=file_path.stem,
            format=".txt",
            file_path=str(file_path),
            file_size_bytes=len(raw),
        )
        return ParsedDocument(elements=elements, metadata=metadata)

    def _decode(self, raw: bytes) -> str:
        """Detect encoding: UTF-8 -> charset-normalizer -> Latin-1 fallback."""
        if not raw:
            return ""

        # Try UTF-8 first (most common)
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            pass

        # Use charset-normalizer for detection
        result = from_bytes(raw).best()
        if result is not None:
            return str(result)

        # Latin-1 never fails — ultimate fallback
        return raw.decode("latin-1")

    def _normalize_line_endings(self, text: str) -> str:
        """Convert \\r\\n and \\r to \\n."""
        return text.replace("\r\n", "\n").replace("\r", "\n")

    def _split_paragraphs(self, text: str) -> list[TextElement]:
        """Split text into paragraph elements on double-newlines."""
        # Split on two or more consecutive newlines
        raw_paragraphs = re.split(r"\n{2,}", text.strip())
        elements: list[TextElement] = []
        for para in raw_paragraphs:
            content = para.strip()
            if content:
                elements.append(TextElement(content=content, element_type=ElementType.PARAGRAPH))
        return elements
