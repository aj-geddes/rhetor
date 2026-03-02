"""MainWindow — layout grid, menu bar, keyboard shortcuts, event routing."""

from __future__ import annotations

import logging
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk

from audio.models import PlaybackEvent
from config import AppearanceSettings
from constants import (
    APP_AUTHOR,
    APP_NAME,
    APP_TAGLINE,
    APP_VERSION,
    SUPPORTED_FORMATS,
)
from core.models import ParsedDocument, ReadingChunk
from tts.models import VoiceInfo
from ui.document_view import DocumentView
from ui.status_bar import StatusBar
from ui.toolbar import Toolbar

if TYPE_CHECKING:
    from app import RhetorApp
    from core.reading_session import ReadingSession

log = logging.getLogger(__name__)


class MainWindow(ctk.CTkFrame):
    """Main application frame — owns toolbar, document view, and status bar."""

    def __init__(self, master: ctk.CTk, app: RhetorApp) -> None:
        super().__init__(master)
        self._app = app
        self._root_window = master

        # ── Menu Bar (native tkinter) ────────────────────────────────

        self._menu_bar = tk.Menu(master)
        master.config(menu=self._menu_bar)

        # File menu
        self._file_menu = tk.Menu(self._menu_bar, tearoff=0)
        self._file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self._on_open)
        self._file_menu.add_separator()
        self._recent_menu = tk.Menu(self._file_menu, tearoff=0)
        self._file_menu.add_cascade(label="Recent Files", menu=self._recent_menu)
        self._file_menu.add_separator()
        self._file_menu.add_command(label="Settings...", command=self._on_settings)
        self._file_menu.add_separator()
        self._file_menu.add_command(label="Quit", accelerator="Ctrl+Q", command=self._on_quit)
        self._menu_bar.add_cascade(label="File", menu=self._file_menu)

        # Playback menu
        self._playback_menu = tk.Menu(self._menu_bar, tearoff=0)
        self._playback_menu.add_command(
            label="Play/Pause", accelerator="Space", command=self._on_play_pause
        )
        self._playback_menu.add_command(
            label="Stop", accelerator="Escape", command=self._on_stop
        )
        self._playback_menu.add_separator()
        self._playback_menu.add_command(
            label="Previous Chunk", accelerator="Left", command=self._on_skip_back
        )
        self._playback_menu.add_command(
            label="Next Chunk", accelerator="Right", command=self._on_skip_forward
        )
        self._playback_menu.add_separator()
        self._playback_menu.add_command(
            label="Previous Paragraph",
            accelerator="Ctrl+Left",
            command=self._on_skip_paragraph_back,
        )
        self._playback_menu.add_command(
            label="Next Paragraph",
            accelerator="Ctrl+Right",
            command=self._on_skip_paragraph_forward,
        )
        self._menu_bar.add_cascade(label="Playback", menu=self._playback_menu)

        # Help menu
        self._help_menu = tk.Menu(self._menu_bar, tearoff=0)
        self._help_menu.add_command(
            label="User Guide", accelerator="F1", command=self._on_user_guide
        )
        self._help_menu.add_separator()
        self._help_menu.add_command(label="About Rhetor", command=self._on_about)
        self._menu_bar.add_cascade(label="Help", menu=self._help_menu)

        # ── Layout ───────────────────────────────────────────────────

        settings = app.get_settings_manager().settings

        self._toolbar = Toolbar(self, app)
        self._toolbar.pack(fill="x", padx=0, pady=(0, 2))

        # Apply saved speed/volume
        self._toolbar.set_speed(settings.reading.speed)
        self._toolbar.set_volume(settings.reading.volume)

        self._document_view = DocumentView(
            self,
            font_size=settings.appearance.font_size,
            highlight_color=settings.appearance.highlight_color,
        )
        self._document_view.pack(fill="both", expand=True, padx=0, pady=0)

        self._status_bar = StatusBar(self)
        self._status_bar.pack(fill="x", padx=0, pady=(2, 0))

        # ── Keyboard Shortcuts ───────────────────────────────────────

        master.bind("<Control-o>", lambda e: self._on_open())
        master.bind("<Control-q>", lambda e: self._on_quit())
        master.bind("<space>", self._on_space_key)
        master.bind("<Escape>", lambda e: self._on_stop())
        master.bind("<Left>", lambda e: self._on_skip_back())
        master.bind("<Right>", lambda e: self._on_skip_forward())
        master.bind("<Control-Left>", lambda e: self._on_skip_paragraph_back())
        master.bind("<Control-Right>", lambda e: self._on_skip_paragraph_forward())
        master.bind("<Control-Up>", lambda e: self._on_increase_speed())
        master.bind("<Control-Down>", lambda e: self._on_decrease_speed())
        master.bind("<Up>", self._on_up_key)
        master.bind("<Down>", self._on_down_key)
        master.bind("<Control-d>", lambda e: self._on_toggle_theme())
        master.bind("<Control-comma>", lambda e: self._on_settings())
        master.bind("<F1>", lambda e: self._on_user_guide())

        # ── Drag and Drop (optional) ─────────────────────────────────
        self._dnd_enabled = False
        try:
            master.tk.eval("package require tkdnd")
            widget_path = self._document_view._textbox._textbox
            master.tk.eval(
                f"tkdnd::drop_target register {widget_path} DND_Files"
            )
            widget_path.bind("<<DropEnter>>", self._on_drag_enter)
            widget_path.bind("<<DropLeave>>", self._on_drag_leave)
            widget_path.bind("<<Drop>>", self._on_drop)
            self._dnd_enabled = True
        except Exception:
            pass  # DnD silently unavailable

    # ── Public API (called by RhetorApp) ──────────────────────────────

    def load_document(self, document: ParsedDocument, session: ReadingSession) -> None:
        """Load a document into the view and enable controls."""
        self._document_view.load_document(document)
        self._toolbar.set_controls_enabled(True)
        self._status_bar.set_estimated_duration(session.estimated_duration)
        self._status_bar.reset()
        title = document.metadata.title or document.metadata.file_path
        if title:
            self._root_window.title(f"{title} — Rhetor")

    def populate_voices(self, voices: list[VoiceInfo]) -> None:
        """Populate the toolbar voice dropdown."""
        self._toolbar.populate_voices(voices)

    def set_engine_status(self, text: str) -> None:
        """Update the engine status in the status bar."""
        self._status_bar.set_engine_status(text)

    def set_playing_state(self, is_playing: bool, is_paused: bool) -> None:
        """Update toolbar button text for playback state."""
        self._toolbar.set_playing_state(is_playing, is_paused)

    def update_status(self, event: PlaybackEvent) -> None:
        """Update the status bar from a playback event."""
        self._status_bar.update_from_event(event)
        self._status_bar.update_time_remaining(event.chunk_index, event.total_chunks)

    def highlight_chunk(self, chunk: ReadingChunk) -> None:
        """Highlight a chunk in the document view."""
        self._document_view.highlight_chunk(chunk)

    def clear_highlight(self) -> None:
        """Remove chunk highlighting."""
        self._document_view.clear_highlight()

    def show_error(self, message: str) -> None:
        """Show an error in the status bar."""
        self._status_bar.set_error(message)

    def update_recent_files(self, recent_files: list[str]) -> None:
        """Rebuild the recent files submenu."""
        self._recent_menu.delete(0, "end")
        for path in recent_files:
            self._recent_menu.add_command(
                label=path,
                command=self._make_open_recent_cmd(path),
            )

    def _make_open_recent_cmd(self, path: str) -> Callable[[], None]:
        """Create a callback to open a specific recent file."""
        def _open() -> None:
            self._app.open_file(path)
        return _open

    def update_speed_display(self, speed: float) -> None:
        """Update the toolbar speed display."""
        self._toolbar.set_speed(speed)

    def update_volume_display(self, volume: float) -> None:
        """Update the toolbar volume display."""
        self._toolbar.set_volume(volume)

    def show_empty_document(self, file_path: str) -> None:
        """Show an empty document message and disable controls."""
        self._document_view.show_empty_document_message(file_path)
        self._toolbar.set_controls_enabled(False)

    def apply_appearance(self, appearance: AppearanceSettings) -> None:
        """Apply appearance settings to the UI."""
        self._document_view.set_font_size(appearance.font_size)
        self._document_view.set_highlight_color(appearance.highlight_color)

    # ── Internal event handlers ──────────────────────────────────────

    def _on_open(self) -> None:
        self._app.open_file()

    def _on_quit(self) -> None:
        self._app._on_close()

    def _on_play_pause(self) -> None:
        self._app.play_pause()

    def _on_stop(self) -> None:
        self._app.stop()

    def _on_skip_back(self) -> None:
        self._app.skip_back()

    def _on_skip_forward(self) -> None:
        self._app.skip_forward()

    def _on_space_key(self, event: tk.Event) -> str:  # type: ignore[type-arg]
        """Handle space key — play/pause and prevent textbox scrolling."""
        self._app.play_pause()
        return "break"

    def _on_skip_paragraph_back(self) -> None:
        self._app.skip_paragraph_back()

    def _on_skip_paragraph_forward(self) -> None:
        self._app.skip_paragraph_forward()

    def _on_increase_speed(self) -> None:
        self._app.increase_speed()

    def _on_decrease_speed(self) -> None:
        self._app.decrease_speed()

    def _on_up_key(self, event: tk.Event) -> str:  # type: ignore[type-arg]
        """Handle Up key — increase volume and prevent textbox scrolling."""
        self._app.increase_volume()
        return "break"

    def _on_down_key(self, event: tk.Event) -> str:  # type: ignore[type-arg]
        """Handle Down key — decrease volume and prevent textbox scrolling."""
        self._app.decrease_volume()
        return "break"

    def _on_toggle_theme(self) -> None:
        self._app.toggle_theme()

    def _on_user_guide(self) -> None:
        self._app.open_user_guide()

    def _on_about(self) -> None:
        """Show the About Rhetor dialog."""
        messagebox.showinfo(
            f"About {APP_NAME}",
            f"{APP_NAME} v{APP_VERSION}\n\n"
            f"{APP_TAGLINE}\n\n"
            f"Created by {APP_AUTHOR}",
        )

    def _on_settings(self) -> None:
        """Open the settings dialog."""
        from ui.settings_dialog import SettingsDialog

        dialog = SettingsDialog(self._root_window, self._app)
        dialog.grab_set()
        self._root_window.wait_window(dialog)

    # ── Drag and Drop handlers ────────────────────────────────────

    def _on_drag_enter(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        self._document_view.set_drag_highlight(True)

    def _on_drag_leave(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        self._document_view.set_drag_highlight(False)

    def _on_drop(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        self._document_view.set_drag_highlight(False)
        data = str(event.data) if hasattr(event, "data") else ""  # type: ignore[attr-defined]
        # Parse file path (may be wrapped in braces on some platforms)
        file_path = data.strip().strip("{}")
        if not file_path:
            return
        ext = Path(file_path).suffix.lower()
        if ext in SUPPORTED_FORMATS:
            self._app.open_file(file_path)
        else:
            self._status_bar.set_error(f"Unsupported format: {ext}")
