"""StatusBar — displays playback state, progress, and time remaining."""

from __future__ import annotations

from tkinter import messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk

from audio.models import PlaybackEvent, PlaybackState

if TYPE_CHECKING:
    pass


def format_time(seconds: float) -> str:
    """Format seconds into a human-readable time string.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted string like "1:23" or "0:05".
    """
    if seconds < 0:
        seconds = 0
    total = int(seconds)
    minutes = total // 60
    secs = total % 60
    return f"{minutes}:{secs:02d}"


_STATE_LABELS: dict[PlaybackState, str] = {
    PlaybackState.IDLE: "Ready",
    PlaybackState.BUFFERING: "Buffering...",
    PlaybackState.PLAYING: "Playing",
    PlaybackState.PAUSED: "Paused",
    PlaybackState.STOPPED: "Stopped",
    PlaybackState.FINISHED: "Finished",
}


class StatusBar(ctk.CTkFrame):
    """Bottom status bar showing playback state, progress, and engine info."""

    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, height=28)

        self._state_label = ctk.CTkLabel(self, text="Ready", anchor="w", width=100)
        self._state_label.pack(side="left", padx=(8, 4))

        self._separator1 = ctk.CTkLabel(self, text="|", width=10)
        self._separator1.pack(side="left", padx=2)

        self._progress_label = ctk.CTkLabel(self, text="", anchor="w", width=140)
        self._progress_label.pack(side="left", padx=4)

        self._separator2 = ctk.CTkLabel(self, text="|", width=10)
        self._separator2.pack(side="left", padx=2)

        self._time_label = ctk.CTkLabel(self, text="", anchor="w", width=120)
        self._time_label.pack(side="left", padx=4)

        self._engine_label = ctk.CTkLabel(self, text="", anchor="e")
        self._engine_label.pack(side="right", padx=(4, 8))

        self._estimated_total: float = 0.0
        self._last_error: str = ""

    def update_from_event(self, event: PlaybackEvent) -> None:
        """Update the status bar from a playback event."""
        state_text = _STATE_LABELS.get(event.state, str(event.state.name))
        self._state_label.configure(text=state_text)

        if event.total_chunks > 0:
            progress = f"Chunk {event.chunk_index + 1} of {event.total_chunks}"
            self._progress_label.configure(text=progress)
        else:
            self._progress_label.configure(text="")

    def set_estimated_duration(self, total_seconds: float) -> None:
        """Set the total estimated reading duration."""
        self._estimated_total = total_seconds

    def update_time_remaining(self, chunk_index: int, total_chunks: int) -> None:
        """Update estimated time remaining based on progress."""
        if total_chunks <= 0 or self._estimated_total <= 0:
            self._time_label.configure(text="")
            return
        fraction_remaining = max(0.0, 1.0 - (chunk_index / total_chunks))
        remaining = self._estimated_total * fraction_remaining
        self._time_label.configure(text=f"~{format_time(remaining)} remaining")

    def set_engine_status(self, text: str) -> None:
        """Set the engine status label on the right side."""
        self._engine_label.configure(text=text)

    def set_error(self, message: str) -> None:
        """Display an error message in the state label.

        Truncates to 80 chars for display; stores the full message.
        Click the label to see the full error.
        """
        self._last_error = message
        display = message[:80] + ("..." if len(message) > 80 else "")
        self._state_label.configure(text=f"Error: {display}")
        self._state_label.bind("<Button-1>", lambda e: self._show_full_error())

    def _show_full_error(self) -> None:
        """Show the full error message in a dialog."""
        if self._last_error:
            messagebox.showwarning("Error Details", self._last_error)

    def reset(self) -> None:
        """Reset the status bar to its initial state."""
        self._state_label.configure(text="Ready")
        self._progress_label.configure(text="")
        self._time_label.configure(text="")
        self._estimated_total = 0.0
        self._last_error = ""
        self._state_label.unbind("<Button-1>")
