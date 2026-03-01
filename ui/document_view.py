"""DocumentView — text display with chunk highlighting and auto-scroll."""

from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter as ctk

from constants import APP_TAGLINE, DEFAULT_FONT_SIZE, DEFAULT_HIGHLIGHT_COLOR
from core.models import ParsedDocument, ReadingChunk

if TYPE_CHECKING:
    pass


_WELCOME_TEXT = f"""{APP_TAGLINE}

Open a document to get started.

Supported formats:
  - Plain Text (.txt)
  - Markdown (.md)
  - Word Documents (.docx)
  - PDF Documents (.pdf)

Use File > Open or Ctrl+O to open a document.
Press Space to play/pause, Escape to stop.
Press F1 to open the User Guide.
"""


class DocumentView(ctk.CTkFrame):
    """Scrollable text display with chunk highlighting."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        font_size: int = DEFAULT_FONT_SIZE,
        highlight_color: str = DEFAULT_HIGHLIGHT_COLOR,
    ) -> None:
        super().__init__(master)

        self._font_size = font_size
        self._highlight_color = highlight_color
        self._document: ParsedDocument | None = None

        self._textbox = ctk.CTkTextbox(
            self,
            font=("Consolas", font_size),
            wrap="word",
            state="disabled",
            activate_scrollbars=True,
        )
        self._textbox.pack(fill="both", expand=True, padx=4, pady=4)

        # Configure highlight tag
        self._textbox._textbox.tag_configure(
            "current_chunk",
            background=highlight_color,
        )

        self.show_welcome()

    def show_welcome(self) -> None:
        """Display the welcome screen."""
        self._document = None
        self._set_text(_WELCOME_TEXT)

    def load_document(self, document: ParsedDocument) -> None:
        """Load and display a parsed document."""
        self._document = document
        self._set_text(document.full_text)

    def highlight_chunk(self, chunk: ReadingChunk) -> None:
        """Highlight the given chunk and auto-scroll to it."""
        tb = self._textbox._textbox

        # Remove previous highlight
        tb.tag_remove("current_chunk", "1.0", "end")

        # Calculate text indices from character offsets
        start_idx = f"1.0 + {chunk.char_offset_start} chars"
        end_idx = f"1.0 + {chunk.char_offset_end} chars"

        tb.tag_add("current_chunk", start_idx, end_idx)
        tb.see(start_idx)

    def clear_highlight(self) -> None:
        """Remove all highlighting."""
        self._textbox._textbox.tag_remove("current_chunk", "1.0", "end")

    def set_font_size(self, size: int) -> None:
        """Change the display font size."""
        self._font_size = size
        self._textbox.configure(font=("Consolas", size))

    def set_highlight_color(self, color: str) -> None:
        """Change the chunk highlight color."""
        self._highlight_color = color
        self._textbox._textbox.tag_configure("current_chunk", background=color)

    def show_empty_document_message(self, file_path: str) -> None:
        """Display a message for a document that has no readable text."""
        from pathlib import Path

        name = Path(file_path).name
        message = (
            f"No readable text found in:\n"
            f"  {name}\n\n"
            "The file may be empty, scanned, or in an unsupported format.\n"
        )
        self._set_text(message)

    def set_drag_highlight(self, active: bool) -> None:
        """Toggle a visual highlight to indicate drag-and-drop readiness."""
        if active:
            self._textbox.configure(border_width=2)
        else:
            self._textbox.configure(border_width=0)

    def _set_text(self, text: str) -> None:
        """Replace all text in the textbox."""
        self._textbox.configure(state="normal")
        self._textbox.delete("1.0", "end")
        self._textbox.insert("1.0", text)
        self._textbox.configure(state="disabled")
