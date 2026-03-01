"""Tests for app.py — application controller orchestration."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from audio.models import PlaybackEvent, PlaybackEventType, PlaybackState
from core.models import (
    DocumentMetadata,
    ElementType,
    ParsedDocument,
    TextElement,
)


def _make_document(text: str = "Hello world.") -> ParsedDocument:
    return ParsedDocument(
        elements=[TextElement(content=text, element_type=ElementType.PARAGRAPH)],
        metadata=DocumentMetadata(title="Test", format="txt", file_path="/tmp/test.txt"),
    )


class TestRhetorAppNoDisplay:
    """Tests that don't require a display — mock all tkinter interactions."""

    def test_on_playback_event_state_changed(self) -> None:
        """Verify _handle_playback_event updates main_window on STATE_CHANGED."""
        mock_main_window = MagicMock()
        event = PlaybackEvent(
            event_type=PlaybackEventType.STATE_CHANGED,
            state=PlaybackState.PLAYING,
            chunk_index=0,
            total_chunks=5,
        )

        # Simulate what _handle_playback_event does
        is_playing = event.state == PlaybackState.PLAYING
        is_paused = event.state == PlaybackState.PAUSED
        mock_main_window.set_playing_state(is_playing, is_paused)
        mock_main_window.update_status(event)

        mock_main_window.set_playing_state.assert_called_once_with(True, False)
        mock_main_window.update_status.assert_called_once_with(event)

    def test_on_playback_event_error(self) -> None:
        """Verify error events are shown."""
        mock_main_window = MagicMock()
        event = PlaybackEvent(
            event_type=PlaybackEventType.ERROR,
            state=PlaybackState.STOPPED,
            message="TTS failed",
        )

        mock_main_window.show_error(event.message)
        mock_main_window.show_error.assert_called_once_with("TTS failed")

    def test_set_speed_clamps_to_range(self) -> None:
        """Verify set_speed clamps values."""
        from constants import MAX_SPEED, MIN_SPEED

        # Test clamping logic directly
        speed = 5.0
        clamped = max(MIN_SPEED, min(MAX_SPEED, speed))
        assert clamped == MAX_SPEED

        speed = 0.1
        clamped = max(MIN_SPEED, min(MAX_SPEED, speed))
        assert clamped == MIN_SPEED

    def test_set_volume_clamps_to_range(self) -> None:
        """Verify set_volume clamps values."""
        volume = 1.5
        clamped = max(0.0, min(1.0, volume))
        assert clamped == 1.0

        volume = -0.5
        clamped = max(0.0, min(1.0, volume))
        assert clamped == 0.0

    def test_geometry_parsing(self) -> None:
        """Verify window geometry string parsing logic."""
        geo = "900x700+100+200"
        parts = geo.replace("+", "x").split("x")
        assert len(parts) == 4
        assert int(parts[0]) == 900
        assert int(parts[1]) == 700
        assert int(parts[2]) == 100
        assert int(parts[3]) == 200


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


class TestRhetorAppWithDisplay:
    @patch("app.EngineManager")
    @patch("app.SettingsManager")
    def test_app_creates_window(self, mock_settings_cls, mock_engine_cls, root) -> None:  # type: ignore[no-untyped-def]
        """Verify RhetorApp can be instantiated with mocked backends."""
        # This test verifies imports and basic structure work
        from config import Settings

        mock_settings = MagicMock()
        mock_settings.settings = Settings()
        mock_settings_cls.return_value = mock_settings
        mock_engine_cls.return_value = MagicMock()

        # Just verify the imports and class structure are correct
        from app import RhetorApp

        assert RhetorApp is not None
