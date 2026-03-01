"""PDF parser using PyMuPDF (pymupdf)."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pymupdf

from core.models import DocumentMetadata, ElementType, ParsedDocument, TextElement
from core.parsers import FileAccessError, ParserError


class PdfParser:
    """Parse .pdf files with layout-aware text extraction."""

    def parse(self, file_path: Path) -> ParsedDocument:
        if not file_path.exists():
            raise FileAccessError(f"File not found: {file_path}")

        try:
            doc = pymupdf.open(str(file_path))
        except Exception as exc:
            raise ParserError(f"Failed to open PDF: {exc}") from exc

        if doc.is_encrypted:
            try:
                if not doc.authenticate(""):
                    raise ParserError("PDF is password-protected and cannot be opened.")
            except Exception as exc:
                raise ParserError("PDF is password-protected and cannot be opened.") from exc

        repeated = self._detect_repeated_text(doc)
        elements = self._extract_elements(doc, repeated)
        metadata = self._extract_metadata(doc, file_path)
        doc.close()
        return ParsedDocument(elements=elements, metadata=metadata)

    def _extract_elements(
        self, doc: pymupdf.Document, repeated: set[str]
    ) -> list[TextElement]:
        """Extract text page-by-page with header/footer filtering."""
        elements: list[TextElement] = []

        for page in doc:
            # Check for image-only page
            text = page.get_text("text", sort=True).strip()
            if not text:
                if page.get_images():
                    elements.append(
                        TextElement(
                            content="[Image-only page — no extractable text]",
                            element_type=ElementType.PARAGRAPH,
                            metadata={"image_only": "true"},
                        )
                    )
                continue

            # Try table extraction
            tables = page.find_tables()
            table_rects: list[pymupdf.Rect] = []
            if tables and tables.tables:
                for table in tables.tables:
                    table_rects.append(pymupdf.Rect(table.bbox))
                    for row in table.extract():
                        cells = [cell or "" for cell in row]
                        row_text = " | ".join(c.strip() for c in cells)
                        if row_text.replace("|", "").strip():
                            elements.append(
                                TextElement(content=row_text, element_type=ElementType.TABLE)
                            )

            # Extract text blocks with position info for heading detection
            blocks = page.get_text("dict", sort=True)["blocks"]
            for block in blocks:
                if block.get("type") != 0:  # type 0 = text
                    continue

                # Skip text inside table regions
                block_rect = pymupdf.Rect(block["bbox"])
                if any(block_rect.intersects(tr) for tr in table_rects):
                    continue

                for line in block.get("lines", []):
                    spans = line.get("spans", [])
                    if not spans:
                        continue

                    line_text = "".join(s["text"] for s in spans).strip()
                    if not line_text:
                        continue

                    # Skip repeated headers/footers
                    if line_text in repeated:
                        continue

                    # Heading heuristic: larger font size
                    avg_size = sum(s["size"] for s in spans) / len(spans)
                    if avg_size >= 16:
                        elements.append(
                            TextElement(
                                content=line_text,
                                element_type=ElementType.HEADING,
                                level=1 if avg_size >= 20 else 2,
                            )
                        )
                    elif avg_size >= 13:
                        elements.append(
                            TextElement(
                                content=line_text,
                                element_type=ElementType.HEADING,
                                level=3,
                            )
                        )
                    else:
                        elements.append(
                            TextElement(content=line_text, element_type=ElementType.PARAGRAPH)
                        )

        return elements

    def _detect_repeated_text(self, doc: pymupdf.Document) -> set[str]:
        """Find text that repeats on >80% of pages (likely headers/footers)."""
        if len(doc) < 3:
            return set()

        page_texts: list[set[str]] = []
        for page in doc:
            blocks = page.get_text("dict", sort=True).get("blocks", [])
            lines: set[str] = set()
            for block in blocks:
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    text = "".join(s["text"] for s in line.get("spans", [])).strip()
                    if text:
                        lines.add(text)
            page_texts.append(lines)

        # Count how many pages each line appears on
        counter: Counter[str] = Counter()
        for lines in page_texts:
            for line in lines:
                counter[line] += 1

        threshold = len(doc) * 0.8
        return {text for text, count in counter.items() if count >= threshold}

    def _extract_metadata(self, doc: pymupdf.Document, file_path: Path) -> DocumentMetadata:
        meta = doc.metadata or {}
        return DocumentMetadata(
            title=meta.get("title", "") or file_path.stem,
            author=meta.get("author", ""),
            page_count=len(doc),
            format=".pdf",
            file_path=str(file_path),
            file_size_bytes=file_path.stat().st_size,
        )
