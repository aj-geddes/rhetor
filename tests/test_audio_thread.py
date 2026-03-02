"""Tests for TTSWorker and AudioPlayer — pygame fully mocked."""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from audio.audio_thread import (
    AudioPlayer,
    TTSWorker,
    init_mixer,
    is_pygame_available,
    quit_mixer,
)
from audio.buffer import AudioBuffer
from audio.models import (
    AudioChunk,
    AudioPlayerNotAvailableError,
    PlaybackEvent,
    PlaybackEventType,
    PlaybackState,
)
from core.models import ChunkType, ReadingChunk
from tts.base_engine import TTSSynthesisError
from tts.models import AudioFormat, SynthesisResult


def _make_reading_chunks(n: int) -> list[ReadingChunk]:
    return [
        ReadingChunk(
            text=f"Sentence {i}.",
            paragraph_index=0,
            sentence_index=i,
            char_offset_start=i * 12,
            char_offset_end=(i + 1) * 12,
            chunk_type=ChunkType.SENTENCE,
        )
        for i in range(n)
    ]


def _make_audio_chunk(index: int = 0) -> AudioChunk:
    return AudioChunk(audio_data=b"\x00\x01", chunk_index=index, text="hi", format="wav")


def _make_synthesis_result() -> SynthesisResult:
    return SynthesisResult(audio_data=b"\x00\x01", audio_format=AudioFormat.WAV, sample_rate=22050)


# ── is_pygame_available ─────────────────────────────────────────────────────


class TestPygameAvailability:
    def test_returns_bool(self) -> None:
        result = is_pygame_available()
        assert isinstance(result, bool)


# ── init_mixer / quit_mixer ─────────────────────────────────────────────────


class TestMixerInit:
    @patch("audio.audio_thread._PYGAME_AVAILABLE", False)
    def test_init_mixer_raises_when_unavailable(self) -> None:
        with pytest.raises(AudioPlayerNotAvailableError, match="not installed"):
            init_mixer()

    @patch("audio.audio_thread._PYGAME_AVAILABLE", True)
    @patch("audio.audio_thread.pygame")
    def test_init_mixer_calls_pygame(self, mock_pygame: MagicMock) -> None:
        init_mixer(frequency=44100, size=-16, channels=2)
        mock_pygame.mixer.init.assert_called_once_with(frequency=44100, size=-16, channels=2)

    @patch("audio.audio_thread._PYGAME_AVAILABLE", True)
    @patch("audio.audio_thread.pygame")
    def test_init_mixer_wraps_exception(self, mock_pygame: MagicMock) -> None:
        mock_pygame.mixer.init.side_effect = RuntimeError("SDL error")
        with pytest.raises(AudioPlayerNotAvailableError, match="SDL error"):
            init_mixer()

    @patch("audio.audio_thread._PYGAME_AVAILABLE", True)
    @patch("audio.audio_thread.pygame")
    def test_quit_mixer_calls_pygame(self, mock_pygame: MagicMock) -> None:
        quit_mixer()
        mock_pygame.mixer.quit.assert_called_once()

    @patch("audio.audio_thread._PYGAME_AVAILABLE", False)
    def test_quit_mixer_noop_when_unavailable(self) -> None:
        quit_mixer()  # should not raise


# ── TTSWorker ───────────────────────────────────────────────────────────────


class TestTTSWorker:
    def test_synthesizes_all_chunks(self) -> None:
        chunks = _make_reading_chunks(3)
        engine = MagicMock()
        engine.synthesize.return_value = _make_synthesis_result()
        buf = AudioBuffer(capacity=5)
        stop = threading.Event()
        skip = threading.Event()

        worker = TTSWorker(
            engine_manager=engine,
            buffer=buf,
            chunks=chunks,
            start_index=0,
            get_settings=lambda: ("test-voice", 1.0, 0.8),
            stop_event=stop,
            skip_event=skip,
        )
        worker.start()
        worker.join(timeout=5.0)

        assert engine.synthesize.call_count == 3
        assert buf.is_complete
        # All 3 chunks should be in the buffer
        results = []
        while not buf.is_empty:
            c = buf.get(timeout=1.0)
            if c is not None:
                results.append(c)
        assert len(results) == 3
        assert [c.chunk_index for c in results] == [0, 1, 2]

    def test_starts_from_given_index(self) -> None:
        chunks = _make_reading_chunks(5)
        engine = MagicMock()
        engine.synthesize.return_value = _make_synthesis_result()
        buf = AudioBuffer(capacity=5)
        stop = threading.Event()
        skip = threading.Event()

        worker = TTSWorker(
            engine_manager=engine,
            buffer=buf,
            chunks=chunks,
            start_index=3,
            get_settings=lambda: ("v", 1.0, 1.0),
            stop_event=stop,
            skip_event=skip,
        )
        worker.start()
        worker.join(timeout=5.0)

        assert engine.synthesize.call_count == 2  # chunks 3 and 4

    def test_stop_event_halts_worker(self) -> None:
        chunks = _make_reading_chunks(100)
        engine = MagicMock()

        call_count = 0

        def slow_synth(*args: object, **kwargs: object) -> SynthesisResult:
            nonlocal call_count
            call_count += 1
            if call_count >= 3:
                stop.set()
            return _make_synthesis_result()

        engine.synthesize.side_effect = slow_synth
        buf = AudioBuffer(capacity=10)
        stop = threading.Event()
        skip = threading.Event()

        worker = TTSWorker(
            engine_manager=engine,
            buffer=buf,
            chunks=chunks,
            start_index=0,
            get_settings=lambda: ("v", 1.0, 1.0),
            stop_event=stop,
            skip_event=skip,
        )
        worker.start()
        worker.join(timeout=5.0)

        # Worker should have stopped early
        assert call_count < 100

    def test_synthesis_failure_skips_chunk(self) -> None:
        chunks = _make_reading_chunks(3)
        engine = MagicMock()
        engine.synthesize.side_effect = [
            _make_synthesis_result(),
            TTSSynthesisError("network error"),
            _make_synthesis_result(),
        ]
        buf = AudioBuffer(capacity=5)
        stop = threading.Event()
        skip = threading.Event()

        worker = TTSWorker(
            engine_manager=engine,
            buffer=buf,
            chunks=chunks,
            start_index=0,
            get_settings=lambda: ("v", 1.0, 1.0),
            stop_event=stop,
            skip_event=skip,
        )
        worker.start()
        worker.join(timeout=5.0)

        # 2 successful chunks
        results = []
        while not buf.is_empty:
            c = buf.get(timeout=1.0)
            if c is not None:
                results.append(c)
        assert len(results) == 2
        assert results[0].chunk_index == 0
        assert results[1].chunk_index == 2

    def test_current_index_property(self) -> None:
        chunks = _make_reading_chunks(2)
        engine = MagicMock()
        engine.synthesize.return_value = _make_synthesis_result()
        buf = AudioBuffer(capacity=5)
        stop = threading.Event()
        skip = threading.Event()

        worker = TTSWorker(
            engine_manager=engine,
            buffer=buf,
            chunks=chunks,
            start_index=0,
            get_settings=lambda: ("v", 1.0, 1.0),
            stop_event=stop,
            skip_event=skip,
        )
        assert worker.current_index == 0
        worker.start()
        worker.join(timeout=5.0)
        assert worker.current_index == 2  # past last


# ── AudioPlayer ─────────────────────────────────────────────────────────────


class TestAudioPlayer:
    @patch("audio.audio_thread._PYGAME_AVAILABLE", True)
    @patch("audio.audio_thread.pygame")
    def test_plays_chunks_from_buffer(self, mock_pygame: MagicMock) -> None:
        # Setup mock channel
        mock_channel = MagicMock()
        busy_calls = iter([False])
        mock_channel.get_busy.side_effect = lambda: next(busy_calls, False)
        mock_sound = MagicMock()
        mock_sound.play.return_value = mock_channel
        mock_pygame.mixer.Sound.return_value = mock_sound

        buf = AudioBuffer(capacity=3)
        buf.put(_make_audio_chunk(0))
        buf.signal_complete()

        stop = threading.Event()
        pause = threading.Event()
        skip = threading.Event()
        events: list[PlaybackEvent] = []

        player = AudioPlayer(
            buffer=buf,
            total_chunks=1,
            stop_event=stop,
            pause_event=pause,
            skip_event=skip,
            on_event=events.append,
        )
        player.start()
        player.join(timeout=5.0)

        assert player.current_chunk_index == 0
        mock_pygame.mixer.Sound.assert_called_once()
        mock_sound.play.assert_called_once()

    @patch("audio.audio_thread._PYGAME_AVAILABLE", True)
    @patch("audio.audio_thread.pygame")
    def test_emits_state_changed_events(self, mock_pygame: MagicMock) -> None:
        mock_channel = MagicMock()
        mock_channel.get_busy.return_value = False
        mock_sound = MagicMock()
        mock_sound.play.return_value = mock_channel
        mock_pygame.mixer.Sound.return_value = mock_sound

        buf = AudioBuffer(capacity=3)
        buf.put(_make_audio_chunk(0))
        buf.signal_complete()

        stop = threading.Event()
        pause = threading.Event()
        skip = threading.Event()
        events: list[PlaybackEvent] = []

        player = AudioPlayer(
            buffer=buf,
            total_chunks=1,
            stop_event=stop,
            pause_event=pause,
            skip_event=skip,
            on_event=events.append,
        )
        player.start()
        player.join(timeout=5.0)

        event_types = [e.event_type for e in events]
        assert PlaybackEventType.STATE_CHANGED in event_types
        assert PlaybackEventType.CHUNK_STARTED in event_types
        assert PlaybackEventType.CHUNK_FINISHED in event_types
        assert PlaybackEventType.POSITION_CHANGED in event_types

        # Should have PLAYING then FINISHED state changes
        state_events = [e for e in events if e.event_type == PlaybackEventType.STATE_CHANGED]
        states = [e.state for e in state_events]
        assert PlaybackState.PLAYING in states
        assert PlaybackState.FINISHED in states

    @patch("audio.audio_thread._PYGAME_AVAILABLE", True)
    @patch("audio.audio_thread.pygame")
    def test_stop_event_halts_player(self, mock_pygame: MagicMock) -> None:
        buf = AudioBuffer(capacity=3)
        # Don't signal complete — player would wait forever without stop
        stop = threading.Event()
        pause = threading.Event()
        skip = threading.Event()

        player = AudioPlayer(
            buffer=buf,
            total_chunks=10,
            stop_event=stop,
            pause_event=pause,
            skip_event=skip,
        )
        player.start()
        time.sleep(0.1)
        stop.set()
        player.join(timeout=3.0)
        assert not player.is_alive()

    @patch("audio.audio_thread._PYGAME_AVAILABLE", True)
    @patch("audio.audio_thread.pygame")
    def test_finished_on_empty_complete_buffer(self, mock_pygame: MagicMock) -> None:
        buf = AudioBuffer(capacity=3)
        buf.signal_complete()

        stop = threading.Event()
        pause = threading.Event()
        skip = threading.Event()
        events: list[PlaybackEvent] = []

        player = AudioPlayer(
            buffer=buf,
            total_chunks=0,
            stop_event=stop,
            pause_event=pause,
            skip_event=skip,
            on_event=events.append,
        )
        player.start()
        player.join(timeout=3.0)

        state_events = [e for e in events if e.event_type == PlaybackEventType.STATE_CHANGED]
        assert any(e.state == PlaybackState.FINISHED for e in state_events)

    @patch("audio.audio_thread._PYGAME_AVAILABLE", False)
    def test_play_audio_raises_when_pygame_unavailable(self) -> None:
        buf = AudioBuffer(capacity=3)
        buf.put(_make_audio_chunk(0))
        buf.signal_complete()

        stop = threading.Event()
        pause = threading.Event()
        skip = threading.Event()
        events: list[PlaybackEvent] = []

        player = AudioPlayer(
            buffer=buf,
            total_chunks=1,
            stop_event=stop,
            pause_event=pause,
            skip_event=skip,
            on_event=events.append,
        )
        player.start()
        player.join(timeout=5.0)

        # Should emit an error event
        error_events = [e for e in events if e.event_type == PlaybackEventType.ERROR]
        assert len(error_events) >= 1

    @patch("audio.audio_thread._PYGAME_AVAILABLE", True)
    @patch("audio.audio_thread.pygame")
    def test_no_callback_does_not_error(self, mock_pygame: MagicMock) -> None:
        mock_channel = MagicMock()
        mock_channel.get_busy.return_value = False
        mock_sound = MagicMock()
        mock_sound.play.return_value = mock_channel
        mock_pygame.mixer.Sound.return_value = mock_sound

        buf = AudioBuffer(capacity=3)
        buf.put(_make_audio_chunk(0))
        buf.signal_complete()

        stop = threading.Event()
        pause = threading.Event()
        skip = threading.Event()

        player = AudioPlayer(
            buffer=buf,
            total_chunks=1,
            stop_event=stop,
            pause_event=pause,
            skip_event=skip,
            on_event=None,
        )
        player.start()
        player.join(timeout=5.0)
        assert not player.is_alive()

    @patch("audio.audio_thread._PYGAME_AVAILABLE", True)
    @patch("audio.audio_thread.pygame")
    def test_multiple_chunks_played_in_order(self, mock_pygame: MagicMock) -> None:
        mock_channel = MagicMock()
        mock_channel.get_busy.return_value = False
        mock_sound = MagicMock()
        mock_sound.play.return_value = mock_channel
        mock_pygame.mixer.Sound.return_value = mock_sound

        buf = AudioBuffer(capacity=5)
        for i in range(3):
            buf.put(_make_audio_chunk(i))
        buf.signal_complete()

        stop = threading.Event()
        pause = threading.Event()
        skip = threading.Event()
        chunk_indices: list[int] = []

        def track_event(event: PlaybackEvent) -> None:
            if event.event_type == PlaybackEventType.CHUNK_STARTED:
                chunk_indices.append(event.chunk_index)

        player = AudioPlayer(
            buffer=buf,
            total_chunks=3,
            stop_event=stop,
            pause_event=pause,
            skip_event=skip,
            on_event=track_event,
        )
        player.start()
        player.join(timeout=5.0)

        assert chunk_indices == [0, 1, 2]
