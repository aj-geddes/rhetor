"""Audio pipeline worker threads — TTSWorker and AudioPlayer."""

from __future__ import annotations

import contextlib
import logging
import threading
from collections.abc import Callable
from io import BytesIO

from audio.buffer import AudioBuffer
from audio.models import (
    AudioChunk,
    AudioPlaybackError,
    AudioPlayerNotAvailableError,
    PlaybackEvent,
    PlaybackEventType,
    PlaybackState,
)
from core.models import ReadingChunk
from tts.base_engine import TTSSynthesisError
from tts.engine_manager import EngineManager
from tts.models import AudioFormat

log = logging.getLogger(__name__)

# ── pygame availability ─────────────────────────────────────────────────────

try:
    import pygame
    import pygame.mixer

    _PYGAME_AVAILABLE = True
except ImportError:
    _PYGAME_AVAILABLE = False


def is_pygame_available() -> bool:
    """Return True if pygame is installed and importable."""
    return _PYGAME_AVAILABLE


def init_mixer(frequency: int = 22050, size: int = -16, channels: int = 1) -> None:
    """Initialize the pygame mixer for audio playback.

    Args:
        frequency: Sample rate in Hz.
        size: Bit depth (negative = signed).
        channels: Number of audio channels (1 = mono).

    Raises:
        AudioPlayerNotAvailableError: If pygame is not available or init fails.
    """
    if not _PYGAME_AVAILABLE:
        raise AudioPlayerNotAvailableError("pygame is not installed")
    try:
        pygame.mixer.init(frequency=frequency, size=size, channels=channels)
    except Exception as exc:
        raise AudioPlayerNotAvailableError(f"Failed to init pygame mixer: {exc}") from exc


def quit_mixer() -> None:
    """Shut down the pygame mixer if it was initialized."""
    if _PYGAME_AVAILABLE:
        with contextlib.suppress(Exception):
            pygame.mixer.quit()


# ── Format mapping ──────────────────────────────────────────────────────────

_FORMAT_MAP = {
    AudioFormat.MP3: "mp3",
    AudioFormat.WAV: "wav",
    AudioFormat.PCM_RAW: "wav",
}


# ── TTSWorker ───────────────────────────────────────────────────────────────


class TTSWorker(threading.Thread):
    """Daemon thread that synthesizes chunks ahead into the audio buffer.

    Reads from a list of ReadingChunks starting at a given index,
    calls EngineManager.synthesize() for each, and puts AudioChunks
    into the buffer.
    """

    def __init__(
        self,
        engine_manager: EngineManager,
        buffer: AudioBuffer,
        chunks: list[ReadingChunk],
        start_index: int,
        voice_id: str,
        speed: float,
        volume: float,
        stop_event: threading.Event,
        skip_event: threading.Event,
    ) -> None:
        super().__init__(daemon=True, name="rhetor-tts-worker")
        self._engine_manager = engine_manager
        self._buffer = buffer
        self._chunks = chunks
        self._index = start_index
        self._voice_id = voice_id
        self._speed = speed
        self._volume = volume
        self._stop_event = stop_event
        self._skip_event = skip_event

    @property
    def current_index(self) -> int:
        """The next chunk index to synthesize."""
        return self._index

    def set_position(self, index: int) -> None:
        """Update the synthesis position (called after skip)."""
        self._index = index

    def run(self) -> None:
        """Synthesize chunks until stopped or all chunks are processed."""
        while self._index < len(self._chunks) and not self._stop_event.is_set():
            if self._skip_event.is_set():
                self._skip_event.clear()
                continue

            chunk = self._chunks[self._index]

            try:
                result = self._engine_manager.synthesize(
                    text=chunk.text,
                    voice_id=self._voice_id,
                    speed=self._speed,
                    volume=self._volume,
                )
                audio_chunk = AudioChunk(
                    audio_data=result.audio_data,
                    chunk_index=self._index,
                    text=chunk.text,
                    format=_FORMAT_MAP.get(result.audio_format, "wav"),
                )

                # Block until space in buffer or stop signal
                while not self._stop_event.is_set():
                    if self._skip_event.is_set():
                        break
                    if self._buffer.put(audio_chunk, timeout=0.2):
                        break
                else:
                    break

                if self._skip_event.is_set():
                    continue

            except TTSSynthesisError as exc:
                log.warning("Synthesis failed for chunk %d: %s — skipping", self._index, exc)

            self._index += 1

        self._buffer.signal_complete()


# ── AudioPlayer ─────────────────────────────────────────────────────────────

EventCallback = Callable[[PlaybackEvent], None]


class AudioPlayer(threading.Thread):
    """Daemon thread that plays AudioChunks from the buffer via pygame.

    Emits PlaybackEvent callbacks for state changes and chunk progress.
    """

    def __init__(
        self,
        buffer: AudioBuffer,
        total_chunks: int,
        stop_event: threading.Event,
        pause_event: threading.Event,
        skip_event: threading.Event,
        on_event: EventCallback | None = None,
    ) -> None:
        super().__init__(daemon=True, name="rhetor-audio-player")
        self._buffer = buffer
        self._total_chunks = total_chunks
        self._stop_event = stop_event
        self._pause_event = pause_event
        self._skip_event = skip_event
        self._on_event = on_event
        self._current_chunk_index = -1

    @property
    def current_chunk_index(self) -> int:
        """Index of the chunk currently being played (or last played)."""
        return self._current_chunk_index

    def _emit(self, event_type: PlaybackEventType, state: PlaybackState, **kwargs: object) -> None:
        """Emit a playback event via the callback, if registered."""
        if self._on_event is not None:
            event = PlaybackEvent(
                event_type=event_type,
                state=state,
                chunk_index=self._current_chunk_index,
                total_chunks=self._total_chunks,
                message=str(kwargs.get("message", "")),
            )
            try:
                self._on_event(event)
            except Exception:
                log.exception("Error in playback event callback")

    def run(self) -> None:
        """Pull chunks from buffer and play them until done or stopped."""
        first_chunk = True

        while not self._stop_event.is_set():
            # Handle pause
            while self._pause_event.is_set() and not self._stop_event.is_set():
                if self._skip_event.is_set():
                    break
                self._pause_event.wait(timeout=0.1)
                # Re-check — wait(timeout) returns immediately if set
                if not self._pause_event.is_set():
                    break

            if self._stop_event.is_set():
                break

            chunk = self._buffer.get(timeout=0.2)
            if chunk is None:
                if self._buffer.is_complete:
                    self._emit(
                        PlaybackEventType.STATE_CHANGED,
                        PlaybackState.FINISHED,
                    )
                    break
                continue

            if first_chunk:
                self._emit(
                    PlaybackEventType.STATE_CHANGED,
                    PlaybackState.PLAYING,
                )
                first_chunk = False

            self._current_chunk_index = chunk.chunk_index
            self._emit(
                PlaybackEventType.CHUNK_STARTED,
                PlaybackState.PLAYING,
            )
            self._emit(
                PlaybackEventType.POSITION_CHANGED,
                PlaybackState.PLAYING,
            )

            try:
                self._play_audio(chunk)
            except AudioPlaybackError as exc:
                log.warning("Playback failed for chunk %d: %s", chunk.chunk_index, exc)
                self._emit(
                    PlaybackEventType.ERROR,
                    PlaybackState.PLAYING,
                    message=str(exc),
                )

            self._emit(
                PlaybackEventType.CHUNK_FINISHED,
                PlaybackState.PLAYING,
            )

        self._stop_playback()

    def _play_audio(self, chunk: AudioChunk) -> None:
        """Play a single audio chunk via pygame.mixer.Sound."""
        if not _PYGAME_AVAILABLE:
            raise AudioPlaybackError("pygame is not installed")

        try:
            sound = pygame.mixer.Sound(BytesIO(chunk.audio_data))
            channel = sound.play()
            if channel is None:
                raise AudioPlaybackError("No available mixer channel")

            # Wait for playback to finish, checking for stop/skip
            while channel.get_busy():
                if self._stop_event.is_set() or self._skip_event.is_set():
                    channel.stop()
                    if self._skip_event.is_set():
                        self._skip_event.clear()
                    return
                if self._pause_event.is_set():
                    channel.pause()
                    while self._pause_event.is_set() and not self._stop_event.is_set():
                        if self._skip_event.is_set():
                            channel.stop()
                            self._skip_event.clear()
                            return
                        self._stop_event.wait(timeout=0.05)
                    if not self._stop_event.is_set():
                        channel.unpause()
                self._stop_event.wait(timeout=0.02)
        except AudioPlaybackError:
            raise
        except Exception as exc:
            raise AudioPlaybackError(f"Playback error: {exc}") from exc

    def _stop_playback(self) -> None:
        """Stop any currently playing audio."""
        if _PYGAME_AVAILABLE:
            with contextlib.suppress(Exception):
                pygame.mixer.stop()
