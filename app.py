"""Rhetor application controller — owns the root window and backend services."""

from __future__ import annotations

import contextlib
import logging
import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk

from audio.models import PlaybackEvent, PlaybackEventType, PlaybackState
from audio.player import PlaybackController
from config import SettingsManager
from constants import (
    FORMAT_DESCRIPTIONS,
    MAX_SPEED,
    MIN_SPEED,
    SPEED_INCREMENT,
    SUPPORTED_FORMATS,
    VOLUME_INCREMENT,
    WINDOW_TITLE,
)
from core.document_loader import load_document
from core.reading_session import ReadingSession
from tts.engine_manager import EngineManager
from tts.models import VoiceInfo
from ui.main_window import MainWindow

log = logging.getLogger(__name__)


class RhetorApp:
    """Main application class — manages root window, backend, and event routing."""

    def __init__(self) -> None:
        self._settings_mgr = SettingsManager()
        self._engine_manager = EngineManager()
        self._playback: PlaybackController | None = None
        self._session: ReadingSession | None = None
        self._voices: list[VoiceInfo] = []
        self._engine_ready = False

        # Build root window
        self._root = ctk.CTk()
        self._root.title(WINDOW_TITLE)

        # Apply appearance settings
        appearance = self._settings_mgr.settings.appearance
        ctk.set_appearance_mode(appearance.theme)

        # Window geometry
        width = appearance.window_width
        height = appearance.window_height
        if appearance.window_x is not None and appearance.window_y is not None:
            self._root.geometry(f"{width}x{height}+{appearance.window_x}+{appearance.window_y}")
        else:
            self._root.geometry(f"{width}x{height}")

        # Build main window frame
        self._main_window = MainWindow(self._root, self)
        self._main_window.pack(fill="both", expand=True)

        # Protocol for window close
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

    def run(self) -> None:
        """Start the application event loop."""
        # Initialize TTS engines in background thread
        self._init_engines_async()
        self._root.mainloop()

    # ── Public API for MainWindow callbacks ────────────────────────────

    def open_file(self, file_path: str | None = None) -> None:
        """Open a document file for reading."""
        if file_path is None:
            filetypes = [
                (f"{desc} (*{ext})", f"*{ext}")
                for ext, desc in FORMAT_DESCRIPTIONS.items()
            ]
            filetypes.insert(0, ("All Supported", " ".join(f"*{e}" for e in SUPPORTED_FORMATS)))
            path = filedialog.askopenfilename(
                title="Open Document",
                filetypes=filetypes,
            )
            if not path:
                return
            file_path = path

        try:
            document = load_document(file_path)
        except Exception as exc:
            messagebox.showerror("Error Opening File", str(exc))
            return

        self._session = ReadingSession(document)

        if self._session.total_chunks == 0:
            self._main_window.show_empty_document(file_path)
            return

        self._main_window.load_document(document, self._session)

        # Load into playback controller
        if self._playback is not None:
            voice_settings = self._settings_mgr.settings.voice
            reading_settings = self._settings_mgr.settings.reading
            self._playback.load_session(
                self._session,
                voice_id=voice_settings.preferred_voice_id,
                speed=reading_settings.speed,
                volume=reading_settings.volume,
            )

        self._settings_mgr.add_recent_file(file_path)
        self._settings_mgr.save()
        self._main_window.update_recent_files(self._settings_mgr.settings.recent_files)

    def play_pause(self) -> None:
        """Toggle play/pause state."""
        if self._playback is None or self._session is None:
            return
        state = self._playback.state
        if state == PlaybackState.PLAYING:
            self._playback.pause()
        elif state == PlaybackState.PAUSED:
            self._playback.resume()
        else:
            try:
                self._playback.start()
            except Exception as exc:
                messagebox.showerror("Playback Error", str(exc))

    def stop(self) -> None:
        """Stop playback."""
        if self._playback is not None:
            self._playback.stop()
        if self._session is not None:
            self._session.reset()
            self._main_window.clear_highlight()

    def skip_forward(self) -> None:
        """Skip to next chunk."""
        if self._playback is not None:
            self._playback.skip_forward()

    def skip_back(self) -> None:
        """Skip to previous chunk."""
        if self._playback is not None:
            self._playback.skip_back()

    def skip_paragraph_forward(self) -> None:
        """Skip to the next paragraph."""
        if self._playback is not None:
            self._playback.skip_paragraph_forward()

    def skip_paragraph_back(self) -> None:
        """Skip to the previous paragraph."""
        if self._playback is not None:
            self._playback.skip_paragraph_back()

    def increase_speed(self) -> None:
        """Increase playback speed by one step."""
        current = self._settings_mgr.settings.reading.speed
        new_speed = min(MAX_SPEED, current + SPEED_INCREMENT)
        self.set_speed(new_speed)
        self._main_window.update_speed_display(new_speed)

    def decrease_speed(self) -> None:
        """Decrease playback speed by one step."""
        current = self._settings_mgr.settings.reading.speed
        new_speed = max(MIN_SPEED, current - SPEED_INCREMENT)
        self.set_speed(new_speed)
        self._main_window.update_speed_display(new_speed)

    def increase_volume(self) -> None:
        """Increase volume by one step."""
        current = self._settings_mgr.settings.reading.volume
        new_volume = min(1.0, current + VOLUME_INCREMENT)
        self.set_volume(new_volume)
        self._main_window.update_volume_display(new_volume)

    def decrease_volume(self) -> None:
        """Decrease volume by one step."""
        current = self._settings_mgr.settings.reading.volume
        new_volume = max(0.0, current - VOLUME_INCREMENT)
        self.set_volume(new_volume)
        self._main_window.update_volume_display(new_volume)

    def toggle_theme(self) -> None:
        """Toggle between dark and light theme."""
        appearance = self._settings_mgr.settings.appearance
        appearance.theme = "light" if appearance.theme == "dark" else "dark"
        self.apply_settings()

    def open_user_guide(self) -> None:
        """Open the user guide dialog."""
        from ui.user_guide import UserGuideDialog

        UserGuideDialog(self._root)

    def set_voice(self, voice_id: str) -> None:
        """Change the active voice."""
        if self._playback is not None:
            self._playback.set_voice(voice_id)
        self._settings_mgr.settings.voice.preferred_voice_id = voice_id
        self._settings_mgr.save()

    def set_speed(self, speed: float) -> None:
        """Change playback speed."""
        speed = max(MIN_SPEED, min(MAX_SPEED, speed))
        if self._playback is not None:
            self._playback.set_speed(speed)
        self._settings_mgr.settings.reading.speed = speed

    def set_volume(self, volume: float) -> None:
        """Change playback volume."""
        volume = max(0.0, min(1.0, volume))
        if self._playback is not None:
            self._playback.set_volume(volume)
        self._settings_mgr.settings.reading.volume = volume

    def get_settings_manager(self) -> SettingsManager:
        """Return the settings manager for the settings dialog."""
        return self._settings_mgr

    def get_voices(self) -> list[VoiceInfo]:
        """Return available voices."""
        return self._voices

    def get_session(self) -> ReadingSession | None:
        """Return the current reading session."""
        return self._session

    def apply_settings(self) -> None:
        """Apply changed settings to the UI and backend."""
        appearance = self._settings_mgr.settings.appearance
        ctk.set_appearance_mode(appearance.theme)
        self._main_window.apply_appearance(appearance)
        self._settings_mgr.save()

    # ── Engine initialization (background thread) ─────────────────────

    def _init_engines_async(self) -> None:
        """Initialize TTS engines in a background thread."""
        thread = threading.Thread(target=self._init_engines_worker, daemon=True)
        thread.start()

    def _init_engines_worker(self) -> None:
        """Worker thread: initialize engines, then schedule UI update."""
        voice_settings = self._settings_mgr.settings.voice
        try:
            self._engine_manager.initialize(
                preferred_engine=voice_settings.preferred_engine,
                force_offline=voice_settings.force_offline,
            )
            self._voices = self._engine_manager.get_available_voices()
            self._engine_ready = True
        except Exception:
            log.exception("Failed to initialize TTS engines")
            self._voices = []
            self._engine_ready = False

        self._root.after(0, self._on_engines_ready)

    def _on_engines_ready(self) -> None:
        """Called on main thread after engine initialization completes."""
        if self._engine_ready:
            self._playback = PlaybackController(
                engine_manager=self._engine_manager,
                on_event=self._on_playback_event,
            )
            self._main_window.populate_voices(self._voices)
            self._main_window.set_engine_status(
                f"Engine: {self._engine_manager.active_engine or 'none'}"
            )
        else:
            self._main_window.set_engine_status("TTS engines unavailable")

    # ── Playback event dispatch (thread → main thread) ────────────────

    def _on_playback_event(self, event: PlaybackEvent) -> None:
        """Called from worker threads — marshals to main thread via root.after()."""
        with contextlib.suppress(RuntimeError):
            self._root.after(0, self._handle_playback_event, event)

    def _handle_playback_event(self, event: PlaybackEvent) -> None:
        """Handle playback events on the main thread."""
        if event.event_type == PlaybackEventType.STATE_CHANGED:
            is_playing = event.state == PlaybackState.PLAYING
            is_paused = event.state == PlaybackState.PAUSED
            self._main_window.set_playing_state(is_playing, is_paused)
            self._main_window.update_status(event)

        elif event.event_type == PlaybackEventType.CHUNK_STARTED:
            if self._session is not None:
                chunk = self._session.current_chunk
                if chunk is not None:
                    self._main_window.highlight_chunk(chunk)
            self._main_window.update_status(event)

        elif event.event_type == PlaybackEventType.POSITION_CHANGED:
            self._main_window.update_status(event)

        elif event.event_type == PlaybackEventType.ERROR:
            self._main_window.show_error(event.message)

    # ── Window lifecycle ──────────────────────────────────────────────

    def _on_close(self) -> None:
        """Handle window close — shutdown playback, save geometry, destroy."""
        if self._playback is not None:
            self._playback.shutdown()

        # Save window geometry
        try:
            geo = self._root.geometry()
            # Format: "WxH+X+Y"
            parts = geo.replace("+", "x").split("x")
            if len(parts) >= 4:
                appearance = self._settings_mgr.settings.appearance
                appearance.window_width = int(parts[0])
                appearance.window_height = int(parts[1])
                appearance.window_x = int(parts[2])
                appearance.window_y = int(parts[3])
                self._settings_mgr.save()
        except (ValueError, IndexError):
            pass

        self._root.destroy()
