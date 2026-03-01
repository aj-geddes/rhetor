"""Tests for ui/user_guide.py — MarkdownRenderer, TextSegment, and dialog."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest

from constants import USER_GUIDE_PATH
from ui.user_guide import MarkdownRenderer, TextSegment

# ── TextSegment ────────────────────────────────────────────────────────────


class TestTextSegment:
    def test_frozen(self) -> None:
        seg = TextSegment(text="hello", tag="body")
        with pytest.raises(AttributeError):
            seg.text = "world"  # type: ignore[misc]

    def test_fields(self) -> None:
        seg = TextSegment(text="hello", tag="h1")
        assert seg.text == "hello"
        assert seg.tag == "h1"


# ── MarkdownRenderer.render() ─────────────────────────────────────────────


class TestMarkdownRendererRender:
    def setup_method(self) -> None:
        self.renderer = MarkdownRenderer()

    def test_h1_heading(self) -> None:
        segments = self.renderer.render("# Title")
        tagged = [s for s in segments if s.tag == "h1"]
        assert len(tagged) == 1
        assert "Title" in tagged[0].text

    def test_h2_heading(self) -> None:
        segments = self.renderer.render("## Subtitle")
        tagged = [s for s in segments if s.tag == "h2"]
        assert len(tagged) == 1
        assert "Subtitle" in tagged[0].text

    def test_h3_heading(self) -> None:
        segments = self.renderer.render("### Section")
        tagged = [s for s in segments if s.tag == "h3"]
        assert len(tagged) == 1
        assert "Section" in tagged[0].text

    def test_h4_maps_to_h3(self) -> None:
        segments = self.renderer.render("#### Deep")
        tagged = [s for s in segments if s.tag == "h3"]
        assert len(tagged) == 1
        assert "Deep" in tagged[0].text

    def test_bold_text(self) -> None:
        segments = self.renderer.render("This is **bold** text.")
        bold = [s for s in segments if s.tag == "bold"]
        assert len(bold) == 1
        assert bold[0].text == "bold"

    def test_inline_code(self) -> None:
        segments = self.renderer.render("Use `Ctrl+O` to open.")
        code = [s for s in segments if s.tag == "code"]
        assert len(code) == 1
        assert code[0].text == "Ctrl+O"

    def test_bullet_list(self) -> None:
        segments = self.renderer.render("- Item one\n- Item two")
        bullets = [s for s in segments if s.tag == "bullet"]
        assert len(bullets) == 2

    def test_numbered_list(self) -> None:
        segments = self.renderer.render("1. First\n2. Second")
        nums = [s for s in segments if s.tag == "numbered"]
        assert len(nums) == 2

    def test_code_block(self) -> None:
        text = "```python\nprint('hello')\n```"
        segments = self.renderer.render(text)
        code = [s for s in segments if s.tag == "code"]
        assert len(code) == 1
        assert "print" in code[0].text

    def test_empty_input(self) -> None:
        segments = self.renderer.render("")
        # Should produce at most whitespace segments
        all_text = "".join(s.text for s in segments)
        assert all_text.strip() == ""

    def test_plain_text(self) -> None:
        segments = self.renderer.render("Just a plain line.")
        body = [s for s in segments if s.tag == "body"]
        combined = "".join(s.text for s in body)
        assert "Just a plain line." in combined

    def test_horizontal_rule(self) -> None:
        segments = self.renderer.render("---")
        body = [s for s in segments if s.tag == "body"]
        combined = "".join(s.text for s in body)
        assert "\u2500" in combined

    def test_table_row(self) -> None:
        text = "| A | B |\n|---|---|\n| 1 | 2 |"
        segments = self.renderer.render(text)
        code = [s for s in segments if s.tag == "code"]
        # Header row + data row, separator skipped
        assert len(code) == 2

    def test_mixed_content(self) -> None:
        text = "# Title\n\nA **bold** paragraph.\n\n- Item"
        segments = self.renderer.render(text)
        tags = {s.tag for s in segments}
        assert "h1" in tags
        assert "bold" in tags
        assert "bullet" in tags

    def test_unclosed_code_block(self) -> None:
        text = "```\ncode here"
        segments = self.renderer.render(text)
        code = [s for s in segments if s.tag == "code"]
        assert len(code) == 1
        assert "code here" in code[0].text


# ── MarkdownRenderer.extract_headings() ───────────────────────────────────


class TestExtractHeadings:
    def setup_method(self) -> None:
        self.renderer = MarkdownRenderer()

    def test_extracts_headings(self) -> None:
        text = "# First\n\n## Second\n\n### Third"
        headings = self.renderer.extract_headings(text)
        assert len(headings) == 3
        assert headings[0] == ("First", "first")
        assert headings[1] == ("Second", "second")
        assert headings[2] == ("Third", "third")

    def test_anchor_formatting(self) -> None:
        text = "## Getting Started"
        headings = self.renderer.extract_headings(text)
        assert headings[0] == ("Getting Started", "getting-started")

    def test_empty_document(self) -> None:
        headings = self.renderer.extract_headings("")
        assert headings == []


# ── USER_GUIDE_PATH ───────────────────────────────────────────────────────


class TestUserGuidePath:
    def test_file_exists(self) -> None:
        assert USER_GUIDE_PATH.exists(), f"User guide not found at {USER_GUIDE_PATH}"

    def test_file_not_empty(self) -> None:
        content = USER_GUIDE_PATH.read_text(encoding="utf-8")
        assert len(content) > 100


# ── UserGuideDialog (display-dependent) ──────────────────────────────────


@pytest.fixture
def root() -> Generator[Any, None, None]:
    """Create a tkinter root window for testing, skip if no display."""
    try:
        import customtkinter as ctk

        root = ctk.CTk()
        root.withdraw()
        yield root
        root.destroy()
    except Exception:
        pytest.skip("No display available for UI tests")


class TestUserGuideDialog:
    def test_dialog_opens(self, root: Any) -> None:
        from ui.user_guide import UserGuideDialog

        dialog = UserGuideDialog(root)
        assert dialog.winfo_exists()
        dialog.destroy()

    def test_dialog_has_content(self, root: Any) -> None:
        from ui.user_guide import UserGuideDialog

        dialog = UserGuideDialog(root)
        content = dialog._textbox.get("1.0", "end").strip()
        assert len(content) > 0
        dialog.destroy()
