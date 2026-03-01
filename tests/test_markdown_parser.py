"""Tests for the markdown parser."""

from pathlib import Path

import pytest

from core.models import ElementType
from core.parsers import FileAccessError
from core.parsers.markdown_parser import MarkdownParser


@pytest.fixture
def parser() -> MarkdownParser:
    return MarkdownParser()


class TestMarkdownParser:
    def test_headings_detected(self, parser: MarkdownParser, md_full: Path) -> None:
        doc = parser.parse(md_full)
        headings = [el for el in doc.elements if el.element_type == ElementType.HEADING]
        assert len(headings) >= 2
        assert headings[0].content == "Main Title"
        assert headings[0].level == 1
        assert headings[1].content == "Section One"
        assert headings[1].level == 2

    def test_bold_stripped(self, parser: MarkdownParser, md_full: Path) -> None:
        doc = parser.parse(md_full)
        paragraphs = [el for el in doc.elements if el.element_type == ElementType.PARAGRAPH]
        bold_para = [p for p in paragraphs if "bold" in p.content]
        assert len(bold_para) >= 1
        assert "**" not in bold_para[0].content

    def test_italic_stripped(self, parser: MarkdownParser, md_full: Path) -> None:
        doc = parser.parse(md_full)
        full = doc.full_text
        assert "italic" in full
        assert "*italic*" not in full

    def test_link_text_kept(self, parser: MarkdownParser, md_full: Path) -> None:
        doc = parser.parse(md_full)
        full = doc.full_text
        assert "link" in full
        assert "https://example.com" not in full

    def test_image_alt_text(self, parser: MarkdownParser, md_full: Path) -> None:
        doc = parser.parse(md_full)
        full = doc.full_text
        assert "image" in full
        assert "pic.png" not in full

    def test_list_items(self, parser: MarkdownParser, md_full: Path) -> None:
        doc = parser.parse(md_full)
        list_items = [el for el in doc.elements if el.element_type == ElementType.LIST_ITEM]
        assert len(list_items) >= 5  # 3 unordered + 2 ordered

    def test_blockquote(self, parser: MarkdownParser, md_full: Path) -> None:
        doc = parser.parse(md_full)
        quotes = [el for el in doc.elements if el.element_type == ElementType.BLOCKQUOTE]
        assert len(quotes) >= 1
        assert "blockquote" in quotes[0].content.lower()

    def test_code_block(self, parser: MarkdownParser, md_full: Path) -> None:
        doc = parser.parse(md_full)
        code = [el for el in doc.elements if el.element_type == ElementType.CODE_BLOCK]
        assert len(code) >= 1
        assert "print" in code[0].content

    def test_horizontal_rule(self, parser: MarkdownParser, md_full: Path) -> None:
        doc = parser.parse(md_full)
        rules = [el for el in doc.elements if el.element_type == ElementType.HORIZONTAL_RULE]
        assert len(rules) >= 1

    def test_html_stripped(self, parser: MarkdownParser, md_full: Path) -> None:
        doc = parser.parse(md_full)
        full = doc.full_text
        assert "<b>" not in full
        assert "HTML" in full

    def test_strikethrough_stripped(self, parser: MarkdownParser, md_full: Path) -> None:
        doc = parser.parse(md_full)
        full = doc.full_text
        assert "strikethrough" in full
        assert "~~" not in full

    def test_inline_code_stripped(self, parser: MarkdownParser, md_full: Path) -> None:
        doc = parser.parse(md_full)
        full = doc.full_text
        assert "code" in full
        # The inline backtick should be gone (but the word "code" in code blocks is fine)

    def test_heading_levels(self, parser: MarkdownParser, md_headings_only: Path) -> None:
        doc = parser.parse(md_headings_only)
        headings = [el for el in doc.elements if el.element_type == ElementType.HEADING]
        assert len(headings) == 4
        assert headings[0].level == 1
        assert headings[1].level == 2
        assert headings[2].level == 3
        assert headings[3].level == 4

    def test_title_from_first_heading(self, parser: MarkdownParser, md_full: Path) -> None:
        doc = parser.parse(md_full)
        assert doc.metadata.title == "Main Title"

    def test_missing_file(self, parser: MarkdownParser, tmp_path: Path) -> None:
        with pytest.raises(FileAccessError):
            parser.parse(tmp_path / "nonexistent.md")
