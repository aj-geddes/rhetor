"""Unified document loading — maps file extensions to parsers."""

from __future__ import annotations

from pathlib import Path

from constants import SUPPORTED_FORMATS
from core.models import ParsedDocument
from core.parsers import FileAccessError, UnsupportedFormatError
from core.parsers.docx_parser import DocxParser
from core.parsers.markdown_parser import MarkdownParser
from core.parsers.pdf_parser import PdfParser
from core.parsers.text_parser import TextParser

_PARSER_MAP = {
    ".txt": TextParser,
    ".md": MarkdownParser,
    ".docx": DocxParser,
    ".pdf": PdfParser,
}


def load_document(file_path: str | Path) -> ParsedDocument:
    """Load and parse a document, dispatching to the correct parser.

    Args:
        file_path: Path to the document file.

    Returns:
        A ParsedDocument with extracted elements and metadata.

    Raises:
        FileAccessError: If the file does not exist.
        UnsupportedFormatError: If the file extension is not supported.
        ParserError: If parsing fails for any other reason.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileAccessError(f"File not found: {path}")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_FORMATS:
        raise UnsupportedFormatError(
            f"Unsupported format '{ext}'. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )

    parser_cls = _PARSER_MAP[ext]
    parser = parser_cls()
    return parser.parse(path)
