"""Tests for ui/toolbar.py — button states, voice population, slider callbacks."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock

import pytest

from tts.models import VoiceInfo


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


@pytest.fixture
def mock_app() -> MagicMock:
    app = MagicMock()
    app.play_pause = MagicMock()
    app.stop = MagicMock()
    app.skip_forward = MagicMock()
    app.skip_back = MagicMock()
    app.set_voice = MagicMock()
    app.set_speed = MagicMock()
    app.set_volume = MagicMock()
    return app


@pytest.fixture
def toolbar(root: Any, mock_app: MagicMock) -> Any:
    from ui.toolbar import Toolbar

    tb = Toolbar(root, mock_app)
    tb.pack()
    return tb


class TestToolbarWidget:
    def test_initial_button_text(self, toolbar) -> None:  # type: ignore[no-untyped-def]
        assert toolbar._play_btn.cget("text") == "Play"

    def test_set_playing_state_playing(self, toolbar) -> None:  # type: ignore[no-untyped-def]
        toolbar.set_playing_state(is_playing=True, is_paused=False)
        assert toolbar._play_btn.cget("text") == "Pause"

    def test_set_playing_state_paused(self, toolbar) -> None:  # type: ignore[no-untyped-def]
        toolbar.set_playing_state(is_playing=False, is_paused=True)
        assert toolbar._play_btn.cget("text") == "Resume"

    def test_set_playing_state_stopped(self, toolbar) -> None:  # type: ignore[no-untyped-def]
        toolbar.set_playing_state(is_playing=False, is_paused=False)
        assert toolbar._play_btn.cget("text") == "Play"

    def test_populate_voices(self, toolbar) -> None:  # type: ignore[no-untyped-def]
        voices = [
            VoiceInfo(
                voice_id="jenny-us",
                name="Jenny",
                engine="edge",
                engine_voice_id="en-US-JennyNeural",
                requires_internet=True,
            ),
            VoiceInfo(
                voice_id="amy-offline",
                name="Amy",
                engine="piper",
                engine_voice_id="en_US-amy-medium",
            ),
        ]
        toolbar.populate_voices(voices)
        assert len(toolbar._voice_map) == 2
        assert toolbar._voice_var.get() == "Jenny (edge)"

    def test_populate_empty_voices(self, toolbar) -> None:  # type: ignore[no-untyped-def]
        toolbar.populate_voices([])
        assert toolbar._voice_var.get() == "(no voices)"

    def test_play_button_calls_app(self, toolbar, mock_app) -> None:  # type: ignore[no-untyped-def]
        toolbar._on_play_pause()
        mock_app.play_pause.assert_called_once()

    def test_stop_button_calls_app(self, toolbar, mock_app) -> None:  # type: ignore[no-untyped-def]
        toolbar._on_stop()
        mock_app.stop.assert_called_once()

    def test_skip_forward_calls_app(self, toolbar, mock_app) -> None:  # type: ignore[no-untyped-def]
        toolbar._on_skip_forward()
        mock_app.skip_forward.assert_called_once()

    def test_skip_back_calls_app(self, toolbar, mock_app) -> None:  # type: ignore[no-untyped-def]
        toolbar._on_skip_back()
        mock_app.skip_back.assert_called_once()

    def test_speed_slider_callback(self, toolbar, mock_app) -> None:  # type: ignore[no-untyped-def]
        toolbar._on_speed_changed(1.5)
        mock_app.set_speed.assert_called_once_with(1.5)
        assert "1.5" in toolbar._speed_label.cget("text")

    def test_volume_slider_callback(self, toolbar, mock_app) -> None:  # type: ignore[no-untyped-def]
        toolbar._on_volume_changed(0.6)
        mock_app.set_volume.assert_called_once_with(0.6)
        assert "60" in toolbar._volume_label.cget("text")

    def test_set_controls_enabled(self, toolbar) -> None:  # type: ignore[no-untyped-def]
        toolbar.set_controls_enabled(True)
        assert toolbar._play_btn.cget("state") == "normal"
        toolbar.set_controls_enabled(False)
        assert toolbar._play_btn.cget("state") == "disabled"
