"""Tests for ui/status_bar.py — pure-logic helpers and widget state."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest

from ui.status_bar import format_time

# ── Pure-logic tests (no display needed) ────────────────────────────────


class TestFormatTime:
    def test_zero_seconds(self) -> None:
        assert format_time(0) == "0:00"

    def test_single_digit_seconds(self) -> None:
        assert format_time(5) == "0:05"

    def test_exact_minute(self) -> None:
        assert format_time(60) == "1:00"

    def test_minute_and_seconds(self) -> None:
        assert format_time(83) == "1:23"

    def test_large_duration(self) -> None:
        assert format_time(3661) == "61:01"

    def test_fractional_seconds(self) -> None:
        assert format_time(90.7) == "1:30"

    def test_negative_clamped_to_zero(self) -> None:
        assert format_time(-10) == "0:00"


# ── Widget tests (require display) ──────────────────────────────────────


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
def status_bar(root: Any) -> Any:
    from ui.status_bar import StatusBar

    bar = StatusBar(root)
    bar.pack()
    return bar


class TestStatusBarWidget:
    def test_initial_state_shows_ready(self, status_bar) -> None:  # type: ignore[no-untyped-def]
        assert status_bar._state_label.cget("text") == "Ready"

    def test_update_from_event(self, status_bar) -> None:  # type: ignore[no-untyped-def]
        from audio.models import PlaybackEvent, PlaybackEventType, PlaybackState

        event = PlaybackEvent(
            event_type=PlaybackEventType.STATE_CHANGED,
            state=PlaybackState.PLAYING,
            chunk_index=2,
            total_chunks=10,
        )
        status_bar.update_from_event(event)
        assert status_bar._state_label.cget("text") == "Playing"
        assert "3 of 10" in status_bar._progress_label.cget("text")

    def test_update_time_remaining(self, status_bar) -> None:  # type: ignore[no-untyped-def]
        status_bar.set_estimated_duration(120.0)
        status_bar.update_time_remaining(5, 10)
        text = status_bar._time_label.cget("text")
        assert "remaining" in text
        assert "1:00" in text

    def test_set_engine_status(self, status_bar) -> None:  # type: ignore[no-untyped-def]
        status_bar.set_engine_status("Engine: edge")
        assert status_bar._engine_label.cget("text") == "Engine: edge"

    def test_set_error(self, status_bar) -> None:  # type: ignore[no-untyped-def]
        status_bar.set_error("something broke")
        assert "Error" in status_bar._state_label.cget("text")

    def test_set_error_truncation(self, status_bar) -> None:  # type: ignore[no-untyped-def]
        long_message = "A" * 200
        status_bar.set_error(long_message)
        text = status_bar._state_label.cget("text")
        # Error prefix + 80 chars + "..."
        assert len(text) < 200
        assert text.endswith("...")

    def test_set_error_stores_full_message(self, status_bar) -> None:  # type: ignore[no-untyped-def]
        msg = "Full error details here"
        status_bar.set_error(msg)
        assert status_bar._last_error == msg

    def test_reset_clears_error(self, status_bar) -> None:  # type: ignore[no-untyped-def]
        status_bar.set_error("fail")
        status_bar.reset()
        assert status_bar._last_error == ""

    def test_reset(self, status_bar) -> None:  # type: ignore[no-untyped-def]
        status_bar.set_error("fail")
        status_bar.reset()
        assert status_bar._state_label.cget("text") == "Ready"
        assert status_bar._progress_label.cget("text") == ""
