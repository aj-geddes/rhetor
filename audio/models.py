"""Audio pipeline data models — playback state, events, and audio chunks."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class PlaybackState(Enum):
    """Current state of the audio playback pipeline."""

    IDLE = auto()
    BUFFERING = auto()
    PLAYING = auto()
    PAUSED = auto()
    STOPPED = auto()
    FINISHED = auto()


class PlaybackEventType(Enum):
    """Types of events emitted by the audio pipeline."""

    STATE_CHANGED = auto()
    CHUNK_STARTED = auto()
    CHUNK_FINISHED = auto()
    POSITION_CHANGED = auto()
    ERROR = auto()


@dataclass(frozen=True, slots=True)
class AudioChunk:
    """Immutable audio data ready for playback.

    Frozen for thread safety — produced by TTSWorker and consumed
    by AudioPlayer on a different thread.
    """

    audio_data: bytes
    chunk_index: int
    text: str
    format: str  # "mp3" or "wav"


@dataclass(frozen=True, slots=True)
class PlaybackEvent:
    """Immutable event emitted by the playback pipeline.

    Frozen for thread safety — produced on worker threads and
    consumed by UI callbacks on the main thread.
    """

    event_type: PlaybackEventType
    state: PlaybackState
    chunk_index: int = -1
    total_chunks: int = 0
    message: str = ""


# ── Exceptions ──────────────────────────────────────────────────────────────


class AudioError(Exception):
    """Base exception for audio pipeline failures."""


class AudioPlayerNotAvailableError(AudioError):
    """Raised when pygame is not installed or mixer init fails."""


class AudioPlaybackError(AudioError):
    """Raised when playback fails (corrupt data, device error, etc.)."""
