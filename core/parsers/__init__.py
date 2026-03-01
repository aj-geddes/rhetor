"""Document parser protocol and shared exceptions."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from core.models import ParsedDocument


class ParserError(Exception):
    """Base exception for document parsing failures."""


class UnsupportedFormatError(ParserError):
    """Raised when a file format is not supported."""


class FileAccessError(ParserError):
    """Raised when a file cannot be read (missing, permissions, etc.)."""


@runtime_checkable
class BaseParser(Protocol):
    """Structural protocol that all document parsers must satisfy."""

    def parse(self, file_path: Path) -> ParsedDocument:
        """Parse a document file and return structured content."""
        ...
