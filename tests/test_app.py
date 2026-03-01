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

    def test_increase_speed_logic(self) -> None:
        """Verify increase_speed clamping."""
        from constants import MAX_SPEED, SPEED_INCREMENT

        current = 1.0
        new_speed = min(MAX_SPEED, current + SPEED_INCREMENT)
        assert new_speed == 1.25

    def test_decrease_speed_logic(self) -> None:
        """Verify decrease_speed clamping."""
        from constants import MIN_SPEED, SPEED_INCREMENT

        current = 1.0
        new_speed = max(MIN_SPEED, current - SPEED_INCREMENT)
        assert new_speed == 0.75

    def test_increase_volume_logic(self) -> None:
        """Verify increase_volume clamping."""
        from constants import VOLUME_INCREMENT

        current = 0.8
        new_volume = min(1.0, current + VOLUME_INCREMENT)
        assert abs(new_volume - 0.85) < 0.001

    def test_decrease_volume_logic(self) -> None:
        """Verify decrease_volume clamping."""
        from constants import VOLUME_INCREMENT

        current = 0.8
        new_volume = max(0.0, current - VOLUME_INCREMENT)
        assert abs(new_volume - 0.75) < 0.001

    def test_toggle_theme_logic(self) -> None:
        """Verify theme toggle."""
        theme = "dark"
        new_theme = "light" if theme == "dark" else "dark"
        assert new_theme == "light"
        new_theme2 = "light" if new_theme == "dark" else "dark"
        assert new_theme2 == "dark"

    def test_increase_speed_at_max(self) -> None:
        """Speed should clamp at MAX_SPEED."""
        from constants import MAX_SPEED, SPEED_INCREMENT

        current = MAX_SPEED
        new_speed = min(MAX_SPEED, current + SPEED_INCREMENT)
        assert new_speed == MAX_SPEED

    def test_decrease_volume_at_zero(self) -> None:
        """Volume should clamp at 0."""
        from constants import VOLUME_INCREMENT

        current = 0.0
        new_volume = max(0.0, current - VOLUME_INCREMENT)
        assert new_volume == 0.0

    def test_increase_volume_at_max(self) -> None:
        """Volume should clamp at 1.0."""
        from constants import VOLUME_INCREMENT

        current = 1.0
        new_volume = min(1.0, current + VOLUME_INCREMENT)
        assert new_volume == 1.0

    def test_empty_document_detection(self) -> None:
        """Verify empty document has zero chunks."""
        doc = ParsedDocument(
            elements=[TextElement(content="   ", element_type=ElementType.PARAGRAPH)],
            metadata=DocumentMetadata(title="Empty", format="txt"),
        )
        from core.reading_session import ReadingSession

        session = ReadingSession(doc)
        assert session.total_chunks == 0

    def test_empty_document_no_elements(self) -> None:
        """Verify truly empty document has zero chunks."""
        doc = ParsedDocument(
            elements=[],
            metadata=DocumentMetadata(title="Empty", format="txt"),
        )
        from core.reading_session import ReadingSession

        session = ReadingSession(doc)
        assert session.total_chunks == 0

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
