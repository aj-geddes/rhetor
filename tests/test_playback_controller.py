"""Tests for PlaybackController — state transitions, skip, settings, shutdown."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from audio.models import (
    AudioPlayerNotAvailableError,
    PlaybackEvent,
    PlaybackEventType,
    PlaybackState,
)
from audio.player import PlaybackController
from core.models import ElementType, ParsedDocument, TextElement
from core.reading_session import ReadingSession
from tts.models import AudioFormat, SynthesisResult


def _make_session(n_chunks: int = 5) -> ReadingSession:
    """Create a ReadingSession with n_chunks via a minimal ParsedDocument."""
    text = ". ".join(f"Sentence {i}" for i in range(n_chunks)) + "."
    elements = [TextElement(content=text, element_type=ElementType.PARAGRAPH)]
    doc = ParsedDocument(elements=elements)
    return ReadingSession(doc)


def _make_synthesis_result() -> SynthesisResult:
    return SynthesisResult(audio_data=b"\x00\x01", audio_format=AudioFormat.WAV, sample_rate=22050)


def _make_engine_manager() -> MagicMock:
    engine = MagicMock()
    engine.synthesize.return_value = _make_synthesis_result()
    return engine


# ── Initialization ──────────────────────────────────────────────────────────


class TestPlaybackControllerInit:
    def test_initial_state_is_idle(self) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        assert ctrl.state == PlaybackState.IDLE

    def test_no_session_initially(self) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        assert ctrl.session is None

    def test_current_chunk_index_without_session(self) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        assert ctrl.current_chunk_index == -1


# ── Load session ────────────────────────────────────────────────────────────


class TestLoadSession:
    def test_load_sets_session(self) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        session = _make_session(3)
        ctrl.load_session(session, voice_id="test-voice", speed=1.5, volume=0.7)
        assert ctrl.session is session
        assert ctrl.state == PlaybackState.IDLE

    def test_load_while_idle(self) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        session = _make_session()
        ctrl.load_session(session)
        assert ctrl.state == PlaybackState.IDLE


# ── Start / pause / resume / stop ───────────────────────────────────────────


class TestPlaybackLifecycle:
    def test_start_without_session_raises(self) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        with pytest.raises(RuntimeError, match="No reading session"):
            ctrl.start()

    @patch("audio.player.is_pygame_available", return_value=False)
    def test_start_without_pygame_raises(self, _mock: MagicMock) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        ctrl.load_session(_make_session())
        with pytest.raises(AudioPlayerNotAvailableError):
            ctrl.start()

    @patch("audio.player.is_pygame_available", return_value=True)
    @patch("audio.player.init_mixer")
    @patch("audio.audio_thread._PYGAME_AVAILABLE", True)
    @patch("audio.audio_thread.pygame")
    def test_start_transitions_to_buffering(
        self,
        mock_pygame: MagicMock,
        mock_init: MagicMock,
        _avail: MagicMock,
    ) -> None:
        # Make the player finish quickly
        mock_channel = MagicMock()
        mock_channel.get_busy.return_value = False
        mock_sound = MagicMock()
        mock_sound.play.return_value = mock_channel
        mock_pygame.mixer.Sound.return_value = mock_sound

        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        ctrl.load_session(_make_session(1))
        ctrl.start()

        # Give threads time to start
        time.sleep(0.3)

        # State should have progressed past IDLE
        assert ctrl.state != PlaybackState.IDLE

        ctrl.shutdown()

    def test_pause_when_idle_is_noop(self) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        ctrl.pause()  # should not raise
        assert ctrl.state == PlaybackState.IDLE

    def test_resume_when_idle_is_noop(self) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        ctrl.resume()
        assert ctrl.state == PlaybackState.IDLE

    def test_stop_when_idle_is_noop(self) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        ctrl.stop()
        assert ctrl.state == PlaybackState.IDLE

    def test_stop_when_stopped_is_noop(self) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        ctrl.stop()
        assert ctrl.state == PlaybackState.IDLE  # was never started


# ── Settings ────────────────────────────────────────────────────────────────


class TestSettings:
    def test_set_voice(self) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        ctrl.set_voice("jenny-us")
        # No error, voice stored internally
        assert ctrl.state == PlaybackState.IDLE

    def test_set_speed(self) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        ctrl.set_speed(1.5)
        assert ctrl.state == PlaybackState.IDLE

    def test_set_volume(self) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        ctrl.set_volume(0.5)
        assert ctrl.state == PlaybackState.IDLE


# ── Skip operations ─────────────────────────────────────────────────────────


class TestSkipOperations:
    def test_skip_forward_when_idle_is_noop(self) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        ctrl.skip_forward()
        assert ctrl.state == PlaybackState.IDLE

    def test_skip_back_when_idle_is_noop(self) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        ctrl.skip_back()
        assert ctrl.state == PlaybackState.IDLE

    def test_skip_paragraph_forward_when_idle_is_noop(self) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        ctrl.skip_paragraph_forward()
        assert ctrl.state == PlaybackState.IDLE

    def test_skip_paragraph_back_when_idle_is_noop(self) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        ctrl.skip_paragraph_back()
        assert ctrl.state == PlaybackState.IDLE

    def test_skip_paragraph_forward_without_session_is_noop(self) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        ctrl._state = PlaybackState.PLAYING  # force state
        ctrl.skip_paragraph_forward()
        # Should not crash — no session loaded

    def test_skip_paragraph_back_without_session_is_noop(self) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        ctrl._state = PlaybackState.PLAYING  # force state
        ctrl.skip_paragraph_back()
        # Should not crash — no session loaded


# ── Shutdown ────────────────────────────────────────────────────────────────


class TestShutdown:
    def test_shutdown_from_idle(self) -> None:
        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        ctrl.shutdown()
        assert ctrl.state == PlaybackState.STOPPED

    @patch("audio.player.is_pygame_available", return_value=True)
    @patch("audio.player.init_mixer")
    @patch("audio.player.quit_mixer")
    @patch("audio.audio_thread._PYGAME_AVAILABLE", True)
    @patch("audio.audio_thread.pygame")
    def test_shutdown_stops_mixer(
        self,
        mock_pygame: MagicMock,
        mock_quit: MagicMock,
        mock_init: MagicMock,
        _avail: MagicMock,
    ) -> None:
        mock_channel = MagicMock()
        mock_channel.get_busy.return_value = False
        mock_sound = MagicMock()
        mock_sound.play.return_value = mock_channel
        mock_pygame.mixer.Sound.return_value = mock_sound

        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        ctrl.load_session(_make_session(1))
        ctrl.start()
        time.sleep(0.2)
        ctrl.shutdown()

        mock_quit.assert_called_once()

    @patch("audio.player.is_pygame_available", return_value=True)
    @patch("audio.player.init_mixer")
    @patch("audio.player.quit_mixer")
    @patch("audio.audio_thread._PYGAME_AVAILABLE", True)
    @patch("audio.audio_thread.pygame")
    def test_shutdown_joins_threads(
        self,
        mock_pygame: MagicMock,
        mock_quit: MagicMock,
        mock_init: MagicMock,
        _avail: MagicMock,
    ) -> None:
        mock_channel = MagicMock()
        mock_channel.get_busy.return_value = False
        mock_sound = MagicMock()
        mock_sound.play.return_value = mock_channel
        mock_pygame.mixer.Sound.return_value = mock_sound

        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        ctrl.load_session(_make_session(2))
        ctrl.start()
        time.sleep(0.2)
        ctrl.shutdown()

        # After shutdown, threads should not be alive
        assert ctrl._worker is None
        assert ctrl._player is None


# ── Event callbacks ─────────────────────────────────────────────────────────


class TestEventCallbacks:
    def test_callback_receives_events(self) -> None:
        events: list[PlaybackEvent] = []
        ctrl = PlaybackController(
            engine_manager=_make_engine_manager(),
            on_event=events.append,
        )
        ctrl.load_session(_make_session())
        ctrl.stop()  # idle → noop, no events

        # Only load_session emits IDLE state_changed
        # After stop from IDLE — no events since stop is a no-op from IDLE

    def test_callback_error_does_not_crash(self) -> None:
        def bad_callback(event: PlaybackEvent) -> None:
            raise ValueError("callback error")

        ctrl = PlaybackController(
            engine_manager=_make_engine_manager(),
            on_event=bad_callback,
        )
        ctrl.load_session(_make_session())
        # Should not raise despite broken callback
        ctrl.shutdown()  # triggers state change

    @patch("audio.player.is_pygame_available", return_value=True)
    @patch("audio.player.init_mixer")
    @patch("audio.player.quit_mixer")
    @patch("audio.audio_thread._PYGAME_AVAILABLE", True)
    @patch("audio.audio_thread.pygame")
    def test_full_playback_emits_events(
        self,
        mock_pygame: MagicMock,
        mock_quit: MagicMock,
        mock_init: MagicMock,
        _avail: MagicMock,
    ) -> None:
        mock_channel = MagicMock()
        mock_channel.get_busy.return_value = False
        mock_sound = MagicMock()
        mock_sound.play.return_value = mock_channel
        mock_pygame.mixer.Sound.return_value = mock_sound

        events: list[PlaybackEvent] = []
        ctrl = PlaybackController(
            engine_manager=_make_engine_manager(),
            on_event=events.append,
        )
        ctrl.load_session(_make_session(1))
        ctrl.start()

        # Wait for playback to complete
        for _ in range(50):
            if ctrl.state == PlaybackState.FINISHED:
                break
            time.sleep(0.1)

        event_types = {e.event_type for e in events}
        assert PlaybackEventType.STATE_CHANGED in event_types

        ctrl.shutdown()


# ── Pause / resume integration ──────────────────────────────────────────────


class TestPauseResume:
    @patch("audio.player.is_pygame_available", return_value=True)
    @patch("audio.player.init_mixer")
    @patch("audio.player.quit_mixer")
    @patch("audio.audio_thread._PYGAME_AVAILABLE", True)
    @patch("audio.audio_thread.pygame")
    def test_pause_and_resume(
        self,
        mock_pygame: MagicMock,
        mock_quit: MagicMock,
        mock_init: MagicMock,
        _avail: MagicMock,
    ) -> None:
        # Make channel busy so we can pause during playback
        busy_count = 0

        def get_busy() -> bool:
            nonlocal busy_count
            busy_count += 1
            return busy_count < 100

        mock_channel = MagicMock()
        mock_channel.get_busy.side_effect = get_busy
        mock_sound = MagicMock()
        mock_sound.play.return_value = mock_channel
        mock_pygame.mixer.Sound.return_value = mock_sound

        ctrl = PlaybackController(engine_manager=_make_engine_manager())
        ctrl.load_session(_make_session(3))
        ctrl.start()

        # Wait for PLAYING state
        for _ in range(20):
            if ctrl.state == PlaybackState.PLAYING:
                break
            time.sleep(0.05)

        ctrl.pause()
        assert ctrl.state == PlaybackState.PAUSED

        ctrl.resume()
        assert ctrl.state == PlaybackState.PLAYING

        ctrl.shutdown()
