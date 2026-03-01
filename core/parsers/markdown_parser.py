"""Markdown parser — regex-based stripping and element classification."""

from __future__ import annotations

import re
from pathlib import Path

from core.models import DocumentMetadata, ElementType, ParsedDocument, TextElement
from core.parsers import FileAccessError

# ── Regex Patterns ────────────────────────────────────────────────────────────

_FENCED_CODE_BLOCK = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_BLOCKQUOTE = re.compile(r"^>\s*(.*)$", re.MULTILINE)
_UNORDERED_LIST = re.compile(r"^[\s]*[-*+]\s+(.+)$", re.MULTILINE)
_ORDERED_LIST = re.compile(r"^[\s]*\d+\.\s+(.+)$", re.MULTILINE)
_HORIZONTAL_RULE = re.compile(r"^[-*_]{3,}\s*$", re.MULTILINE)

# Inline patterns
_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]+\)")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_BOLD_ASTERISK = re.compile(r"\*\*(.+?)\*\*")
_BOLD_UNDERSCORE = re.compile(r"__(.+?)__")
_ITALIC_ASTERISK = re.compile(r"\*(.+?)\*")
_ITALIC_UNDERSCORE = re.compile(r"(?<!\w)_(.+?)_(?!\w)")
_INLINE_CODE = re.compile(r"`([^`]+)`")
_HTML_TAG = re.compile(r"<[^>]+>")
_STRIKETHROUGH = re.compile(r"~~(.+?)~~")


class MarkdownParser:
    """Parse .md files by stripping formatting and classifying elements."""

    def parse(self, file_path: Path) -> ParsedDocument:
        if not file_path.exists():
            raise FileAccessError(f"File not found: {file_path}")

        try:
            text = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise FileAccessError(f"Cannot read file: {exc}") from exc

        text = text.replace("\r\n", "\n").replace("\r", "\n")
        elements = self._extract_elements(text)

        metadata = DocumentMetadata(
            title=self._extract_title(elements, file_path),
            format=".md",
            file_path=str(file_path),
            file_size_bytes=file_path.stat().st_size,
        )
        return ParsedDocument(elements=elements, metadata=metadata)

    def _extract_elements(self, text: str) -> list[TextElement]:
        """Two-pass extraction: fenced code blocks first, then block elements."""
        elements: list[TextElement] = []

        # Pass 1: Extract fenced code blocks, replace with placeholders
        code_blocks: list[str] = []

        def _replace_code(m: re.Match[str]) -> str:
            code = m.group(0)
            # Strip the ``` fences and optional language tag
            lines = code.split("\n")
            inner = "\n".join(lines[1:-1]) if len(lines) > 2 else ""
            code_blocks.append(inner)
            return f"\x00CODE_BLOCK_{len(code_blocks) - 1}\x00"

        text = _FENCED_CODE_BLOCK.sub(_replace_code, text)

        # Pass 2: Process block-level elements line by line / block by block
        blocks = re.split(r"\n{2,}", text.strip())

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            # Check for code block placeholder
            code_match = re.match(r"^\x00CODE_BLOCK_(\d+)\x00$", block)
            if code_match:
                idx = int(code_match.group(1))
                elements.append(
                    TextElement(content=code_blocks[idx], element_type=ElementType.CODE_BLOCK)
                )
                continue

            # Horizontal rule
            if _HORIZONTAL_RULE.match(block):
                elements.append(
                    TextElement(content="", element_type=ElementType.HORIZONTAL_RULE)
                )
                continue

            # Heading
            heading_match = _HEADING.match(block)
            if heading_match:
                level = len(heading_match.group(1))
                content = self._strip_inline(heading_match.group(2))
                elements.append(
                    TextElement(content=content, element_type=ElementType.HEADING, level=level)
                )
                continue

            # Blockquote (may span multiple lines)
            if block.startswith(">"):
                lines = block.split("\n")
                content_lines = []
                for line in lines:
                    m = _BLOCKQUOTE.match(line)
                    content_lines.append(m.group(1) if m else line)
                content = self._strip_inline(" ".join(content_lines))
                elements.append(
                    TextElement(content=content, element_type=ElementType.BLOCKQUOTE)
                )
                continue

            # List items (unordered or ordered) — each line is a separate element
            list_lines = block.split("\n")
            if _UNORDERED_LIST.match(list_lines[0]) or _ORDERED_LIST.match(list_lines[0]):
                for line in list_lines:
                    um = _UNORDERED_LIST.match(line)
                    om = _ORDERED_LIST.match(line)
                    if um:
                        elements.append(
                            TextElement(
                                content=self._strip_inline(um.group(1)),
                                element_type=ElementType.LIST_ITEM,
                            )
                        )
                    elif om:
                        elements.append(
                            TextElement(
                                content=self._strip_inline(om.group(1)),
                                element_type=ElementType.LIST_ITEM,
                            )
                        )
                    elif line.strip():
                        elements.append(
                            TextElement(
                                content=self._strip_inline(line.strip()),
                                element_type=ElementType.PARAGRAPH,
                            )
                        )
                continue

            # Regular paragraph
            content = self._strip_inline(block.replace("\n", " "))
            if content.strip():
                elements.append(
                    TextElement(content=content.strip(), element_type=ElementType.PARAGRAPH)
                )

        return elements

    def _strip_inline(self, text: str) -> str:
        """Remove inline markdown formatting, preserving text content."""
        text = _IMAGE.sub(r"\1", text)  # ![alt](url) -> alt
        text = _LINK.sub(r"\1", text)  # [text](url) -> text
        text = _STRIKETHROUGH.sub(r"\1", text)
        text = _BOLD_ASTERISK.sub(r"\1", text)
        text = _BOLD_UNDERSCORE.sub(r"\1", text)
        text = _ITALIC_ASTERISK.sub(r"\1", text)
        text = _ITALIC_UNDERSCORE.sub(r"\1", text)
        text = _INLINE_CODE.sub(r"\1", text)
        text = _HTML_TAG.sub("", text)
        return text

    def _extract_title(self, elements: list[TextElement], file_path: Path) -> str:
        """Use the first heading as the document title, or fall back to filename."""
        for el in elements:
            if el.element_type == ElementType.HEADING:
                return el.content
        return file_path.stem
