"""DOCX parser using python-docx."""

from __future__ import annotations

from pathlib import Path

from docx import Document as DocxDocument
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

from core.models import DocumentMetadata, ElementType, ParsedDocument, TextElement
from core.parsers import FileAccessError, ParserError


class DocxParser:
    """Parse .docx files, preserving reading order of paragraphs and tables."""

    def parse(self, file_path: Path) -> ParsedDocument:
        if not file_path.exists():
            raise FileAccessError(f"File not found: {file_path}")

        try:
            doc = DocxDocument(str(file_path))
        except Exception as exc:
            raise ParserError(f"Failed to parse DOCX: {exc}") from exc

        elements = self._extract_elements(doc)
        metadata = self._extract_metadata(doc, file_path)
        return ParsedDocument(elements=elements, metadata=metadata)

    def _extract_elements(self, doc: DocxDocument) -> list[TextElement]:
        """Iterate paragraphs and tables in document-order via the XML body."""
        elements: list[TextElement] = []
        body = doc.element.body

        for child in body:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

            if tag == "p":
                para = Paragraph(child, doc)
                el = self._process_paragraph(para)
                if el is not None:
                    elements.append(el)

            elif tag == "tbl":
                table = Table(child, doc)
                table_elements = self._process_table(table)
                elements.extend(table_elements)

        return elements

    def _process_paragraph(self, para: Paragraph) -> TextElement | None:
        """Convert a DOCX paragraph to a TextElement."""
        text = para.text.strip()
        if not text:
            return None

        style_name = (para.style.name or "").lower() if para.style else ""

        # Detect headings by style name
        if "heading" in style_name:
            level = self._heading_level(style_name)
            return TextElement(content=text, element_type=ElementType.HEADING, level=level)

        # Detect list items
        if "list" in style_name or self._has_numbering(para):
            return TextElement(content=text, element_type=ElementType.LIST_ITEM)

        return TextElement(content=text, element_type=ElementType.PARAGRAPH)

    def _process_table(self, table: Table) -> list[TextElement]:
        """Read table row-by-row, each row becomes a TABLE element."""
        elements: list[TextElement] = []
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            row_text = " | ".join(cells)
            if row_text.replace("|", "").strip():
                elements.append(
                    TextElement(content=row_text, element_type=ElementType.TABLE)
                )
        return elements

    def _heading_level(self, style_name: str) -> int:
        """Extract heading level from style name like 'heading 1', 'heading 2'."""
        for i in range(1, 7):
            if str(i) in style_name:
                return i
        return 1

    def _has_numbering(self, para: Paragraph) -> bool:
        """Check if a paragraph has numbering (bullet/numbered list)."""
        pPr = para._element.find(qn("w:pPr"))
        if pPr is not None:
            numPr = pPr.find(qn("w:numPr"))
            return numPr is not None
        return False

    def _extract_metadata(self, doc: DocxDocument, file_path: Path) -> DocumentMetadata:
        """Pull metadata from the DOCX core properties."""
        props = doc.core_properties
        title = props.title or file_path.stem
        author = props.author or ""
        return DocumentMetadata(
            title=title,
            author=author,
            format=".docx",
            file_path=str(file_path),
            file_size_bytes=file_path.stat().st_size,
        )
