"""MainWindow — layout grid, menu bar, keyboard shortcuts, event routing."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from typing import TYPE_CHECKING

import customtkinter as ctk

from audio.models import PlaybackEvent
from config import AppearanceSettings
from core.models import ParsedDocument, ReadingChunk
from tts.models import VoiceInfo
from ui.document_view import DocumentView
from ui.status_bar import StatusBar
from ui.toolbar import Toolbar

if TYPE_CHECKING:
    from app import RhetorApp
    from core.reading_session import ReadingSession


class MainWindow(ctk.CTkFrame):
    """Main application frame — owns toolbar, document view, and status bar."""

    def __init__(self, master: ctk.CTk, app: RhetorApp) -> None:
        super().__init__(master)
        self._app = app
        self._root = master

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
        self._menu_bar.add_cascade(label="Playback", menu=self._playback_menu)

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

    # ── Public API (called by RhetorApp) ──────────────────────────────

    def load_document(self, document: ParsedDocument, session: ReadingSession) -> None:
        """Load a document into the view and enable controls."""
        self._document_view.load_document(document)
        self._toolbar.set_controls_enabled(True)
        self._status_bar.set_estimated_duration(session.estimated_duration)
        self._status_bar.reset()
        title = document.metadata.title or document.metadata.file_path
        if title:
            self._root.title(f"{title} — Rhetor")

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

    def _on_settings(self) -> None:
        """Open the settings dialog."""
        from ui.settings_dialog import SettingsDialog

        dialog = SettingsDialog(self._root, self._app)
        dialog.grab_set()
        self._root.wait_window(dialog)
