"""User guide dialog — markdown renderer and scrollable help window."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

import customtkinter as ctk

from constants import APP_NAME, APP_TAGLINE, USER_GUIDE_PATH

if TYPE_CHECKING:
    pass


@dataclass(frozen=True, slots=True)
class TextSegment:
    """A segment of rendered text with a tag for formatting."""

    text: str
    tag: str


class MarkdownRenderer:
    """Parse simple markdown into TextSegments for display.

    Pure-logic class — no widget dependency, fully testable without a display.
    """

    def render(self, markdown_text: str) -> list[TextSegment]:
        """Parse markdown into a list of TextSegments."""
        segments: list[TextSegment] = []
        lines = markdown_text.split("\n")
        in_code_block = False
        code_lines: list[str] = []

        for line in lines:
            # Code block toggle
            if line.strip().startswith("```"):
                if in_code_block:
                    segments.append(TextSegment(
                        text="\n".join(code_lines) + "\n\n",
                        tag="code",
                    ))
                    code_lines = []
                    in_code_block = False
                else:
                    in_code_block = True
                continue

            if in_code_block:
                code_lines.append(line)
                continue

            # Headings
            heading_match = re.match(r"^(#{1,6})\s+(.*)", line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2).strip()
                tag = f"h{min(level, 3)}"
                segments.append(TextSegment(text=text + "\n\n", tag=tag))
                continue

            # Horizontal rule
            if re.match(r"^---+\s*$", line):
                segments.append(TextSegment(text="\u2500" * 40 + "\n\n", tag="body"))
                continue

            # Unordered list item
            bullet_match = re.match(r"^(\s*)-\s+(.*)", line)
            if bullet_match:
                text = bullet_match.group(2)
                rendered = self._render_inline(text)
                segments.append(TextSegment(text="  \u2022 ", tag="bullet"))
                segments.extend(rendered)
                segments.append(TextSegment(text="\n", tag="body"))
                continue

            # Ordered list item
            num_match = re.match(r"^(\s*)\d+\.\s+(.*)", line)
            if num_match:
                text = num_match.group(2)
                rendered = self._render_inline(text)
                segments.append(TextSegment(text="  ", tag="numbered"))
                segments.extend(rendered)
                segments.append(TextSegment(text="\n", tag="body"))
                continue

            # Table row
            if line.strip().startswith("|"):
                # Skip separator rows like |---|---|
                if re.match(r"^\|[\s\-:|]+\|$", line.strip()):
                    continue
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                row_text = "  " + "  |  ".join(cells)
                segments.append(TextSegment(text=row_text + "\n", tag="code"))
                continue

            # Empty line
            if not line.strip():
                segments.append(TextSegment(text="\n", tag="body"))
                continue

            # Regular paragraph text with inline formatting
            rendered = self._render_inline(line)
            segments.extend(rendered)
            segments.append(TextSegment(text="\n", tag="body"))

        # Flush any unclosed code block
        if in_code_block and code_lines:
            segments.append(TextSegment(
                text="\n".join(code_lines) + "\n\n",
                tag="code",
            ))

        return segments

    def extract_headings(self, markdown_text: str) -> list[tuple[str, str]]:
        """Extract headings as (text, anchor_id) pairs for TOC."""
        headings: list[tuple[str, str]] = []
        for line in markdown_text.split("\n"):
            match = re.match(r"^(#{1,6})\s+(.*)", line)
            if match:
                text = match.group(2).strip()
                anchor = re.sub(r"[^\w\s-]", "", text.lower())
                anchor = re.sub(r"\s+", "-", anchor).strip("-")
                headings.append((text, anchor))
        return headings

    def _render_inline(self, text: str) -> list[TextSegment]:
        """Render inline formatting: **bold**, `code`, and plain text."""
        segments: list[TextSegment] = []
        # Pattern matches **bold** or `inline code`
        pattern = re.compile(r"(\*\*(.+?)\*\*|`(.+?)`)")
        last_end = 0

        for match in pattern.finditer(text):
            # Plain text before this match
            if match.start() > last_end:
                segments.append(TextSegment(
                    text=text[last_end:match.start()],
                    tag="body",
                ))

            if match.group(2) is not None:
                # **bold**
                segments.append(TextSegment(text=match.group(2), tag="bold"))
            elif match.group(3) is not None:
                # `inline code`
                segments.append(TextSegment(text=match.group(3), tag="code"))

            last_end = match.end()

        # Remaining plain text
        if last_end < len(text):
            segments.append(TextSegment(text=text[last_end:], tag="body"))

        return segments


class UserGuideDialog(ctk.CTkToplevel):
    """Non-modal user guide window with rendered markdown content."""

    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master)
        self.title(f"{APP_NAME} — User Guide")
        self.geometry("700x550")
        self.minsize(500, 400)

        # ── Search bar ────────────────────────────────────────────────
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=8, pady=(8, 4))

        ctk.CTkLabel(search_frame, text="Search:").pack(side="left", padx=(0, 4))

        self._search_var = ctk.StringVar()
        self._search_entry = ctk.CTkEntry(
            search_frame, textvariable=self._search_var, width=250,
        )
        self._search_entry.pack(side="left", padx=(0, 4))
        self._search_entry.bind("<Return>", lambda e: self._find_next())

        find_btn = ctk.CTkButton(
            search_frame, text="Find", width=60, command=self._find_next,
        )
        find_btn.pack(side="left")

        # ── Text display ─────────────────────────────────────────────
        self._textbox = ctk.CTkTextbox(
            self,
            font=("Consolas", 13),
            wrap="word",
            state="disabled",
            activate_scrollbars=True,
        )
        self._textbox.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        # Configure text tags
        tb = self._textbox._textbox
        tb.tag_configure("h1", font=("Consolas", 22, "bold"))
        tb.tag_configure("h2", font=("Consolas", 18, "bold"))
        tb.tag_configure("h3", font=("Consolas", 16, "bold"))
        tb.tag_configure("bold", font=("Consolas", 13, "bold"))
        tb.tag_configure("code", font=("Consolas", 12))
        tb.tag_configure("bullet", lmargin1=20, lmargin2=36)
        tb.tag_configure("numbered", lmargin1=20, lmargin2=36)
        tb.tag_configure("body", font=("Consolas", 13))
        tb.tag_configure("search_highlight", background="#d4a843")

        # ── Load and render content ──────────────────────────────────
        self._renderer = MarkdownRenderer()
        self._search_pos = "1.0"
        self._load_content()

        # Keyboard shortcut
        self.bind("<Control-f>", lambda e: self._search_entry.focus_set())

    def _load_content(self) -> None:
        """Load and render the user guide markdown."""
        try:
            content = USER_GUIDE_PATH.read_text(encoding="utf-8")
        except (OSError, FileNotFoundError):
            content = (
                f"# {APP_NAME} User Guide\n\n"
                f"{APP_TAGLINE}\n\n"
                "The user guide file could not be found.\n\n"
                "Use **File > Open** or **Ctrl+O** to open a document.\n"
                "Press **Space** to play/pause reading.\n"
            )

        segments = self._renderer.render(content)
        self._textbox.configure(state="normal")
        self._textbox.delete("1.0", "end")

        for segment in segments:
            self._textbox._textbox.insert("end", segment.text, segment.tag)

        self._textbox.configure(state="disabled")

    def _find_next(self) -> None:
        """Find the next occurrence of the search term."""
        tb = self._textbox._textbox
        term = self._search_var.get()
        if not term:
            return

        # Clear previous highlights
        tb.tag_remove("search_highlight", "1.0", "end")

        pos = tb.search(term, self._search_pos, nocase=True, stopindex="end")
        if not pos:
            # Wrap around
            pos = tb.search(term, "1.0", nocase=True, stopindex="end")

        if pos:
            end_pos = f"{pos}+{len(term)}c"
            tb.tag_add("search_highlight", pos, end_pos)
            tb.see(pos)
            self._search_pos = end_pos
        else:
            self._search_pos = "1.0"
