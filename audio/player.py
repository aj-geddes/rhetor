"""PlaybackController — public API for audio playback orchestration."""

from __future__ import annotations

import logging
import threading

from audio.audio_thread import (
    AudioPlayer,
    EventCallback,
    TTSWorker,
    init_mixer,
    is_pygame_available,
    quit_mixer,
    stop_all_playback,
)
from audio.buffer import AudioBuffer
from audio.models import (
    AudioPlayerNotAvailableError,
    PlaybackEvent,
    PlaybackEventType,
    PlaybackState,
)
from core.reading_session import ReadingSession
from tts.engine_manager import EngineManager

log = logging.getLogger(__name__)


class PlaybackController:
    """Thread-safe public API for document playback.

    Owns the TTSWorker thread, AudioPlayer thread, and AudioBuffer.
    All public methods are safe to call from any thread.
    """

    def __init__(
        self,
        engine_manager: EngineManager,
        on_event: EventCallback | None = None,
    ) -> None:
        self._engine_manager = engine_manager
        self._on_event = on_event
        self._state = PlaybackState.IDLE
        self._lock = threading.Lock()

        self._session: ReadingSession | None = None
        self._voice_id: str = ""
        self._speed: float = 1.0
        self._volume: float = 1.0

        self._buffer: AudioBuffer | None = None
        self._worker: TTSWorker | None = None
        self._player: AudioPlayer | None = None

        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._skip_event = threading.Event()

        self._mixer_initialized = False

    @property
    def state(self) -> PlaybackState:
        """Current playback state."""
        return self._state

    @property
    def current_chunk_index(self) -> int:
        """Index of the chunk currently being played, or -1."""
        if self._player is not None:
            return self._player.current_chunk_index
        return -1

    @property
    def session(self) -> ReadingSession | None:
        """The currently loaded reading session."""
        return self._session

    def load_session(
        self,
        session: ReadingSession,
        voice_id: str = "",
        speed: float = 1.0,
        volume: float = 1.0,
    ) -> None:
        """Load a reading session for playback.

        If playback is active, it is stopped first.

        Args:
            session: The reading session containing chunks to play.
            voice_id: TTS voice identifier.
            speed: Playback speed multiplier.
            volume: Volume level (0.0–1.0).
        """
        with self._lock:
            if self._state not in (PlaybackState.IDLE, PlaybackState.STOPPED, PlaybackState.FINISHED):
                self._stop_internal()

            self._session = session
            self._voice_id = voice_id
            self._speed = speed
            self._volume = volume
            self._set_state(PlaybackState.IDLE)

    def start(self) -> None:
        """Begin playback from the current session position.

        Raises:
            AudioPlayerNotAvailableError: If pygame is not available.
            RuntimeError: If no session is loaded.
        """
        with self._lock:
            if self._session is None:
                raise RuntimeError("No reading session loaded")

            if self._state == PlaybackState.PLAYING:
                return

            if self._state == PlaybackState.PAUSED:
                self._resume_internal()
                return

            if not is_pygame_available():
                raise AudioPlayerNotAvailableError("pygame is not installed")

            self._init_mixer_if_needed()
            self._start_playback()

    def pause(self) -> None:
        """Pause playback. No-op if not playing."""
        with self._lock:
            if self._state != PlaybackState.PLAYING:
                return
            self._pause_event.set()
            self._set_state(PlaybackState.PAUSED)

    def resume(self) -> None:
        """Resume playback. No-op if not paused."""
        with self._lock:
            if self._state != PlaybackState.PAUSED:
                return
            self._resume_internal()

    def stop(self) -> None:
        """Stop playback and reset position."""
        with self._lock:
            if self._state in (PlaybackState.IDLE, PlaybackState.STOPPED):
                return
            self._stop_internal()

    def skip_forward(self) -> None:
        """Skip to the next chunk."""
        with self._lock:
            if self._state not in (PlaybackState.PLAYING, PlaybackState.PAUSED):
                return
            if self._session is None:
                return

            self._session.advance()

            if self._session.is_finished:
                self._stop_internal()
                self._set_state(PlaybackState.FINISHED)
                return

            self._restart_from_position(self._session.position)

    def skip_back(self) -> None:
        """Skip to the previous chunk."""
        with self._lock:
            if self._state not in (PlaybackState.PLAYING, PlaybackState.PAUSED):
                return
            if self._session is None:
                return

            self._session.go_back()
            self._restart_from_position(self._session.position)

    def skip_paragraph_forward(self) -> None:
        """Skip to the first chunk of the next paragraph."""
        with self._lock:
            if self._state not in (PlaybackState.PLAYING, PlaybackState.PAUSED):
                return
            if self._session is None:
                return

            self._session.skip_to_next_paragraph()

            if self._session.is_finished:
                self._stop_internal()
                self._set_state(PlaybackState.FINISHED)
                return

            self._restart_from_position(self._session.position)

    def skip_paragraph_back(self) -> None:
        """Skip to the start of the current or previous paragraph."""
        with self._lock:
            if self._state not in (PlaybackState.PLAYING, PlaybackState.PAUSED):
                return
            if self._session is None:
                return

            self._session.skip_to_prev_paragraph()
            self._restart_from_position(self._session.position)

    def set_voice(self, voice_id: str) -> None:
        """Change the TTS voice. Takes effect on the next chunk."""
        with self._lock:
            self._voice_id = voice_id

    def set_speed(self, speed: float) -> None:
        """Change the playback speed. Takes effect on the next chunk."""
        with self._lock:
            self._speed = speed

    def set_volume(self, volume: float) -> None:
        """Change the volume level. Takes effect on the next chunk."""
        with self._lock:
            self._volume = volume

    def shutdown(self) -> None:
        """Stop playback and release all resources."""
        with self._lock:
            self._stop_event.set()
            stop_all_playback()
            worker = self._worker
            player = self._player
            self._worker = None
            self._player = None

        # Join outside the lock so player callbacks don't deadlock.
        if worker is not None:
            worker.join(timeout=2.0)
        if player is not None:
            player.join(timeout=2.0)

        with self._lock:
            if self._buffer is not None:
                self._buffer.reset()
                self._buffer = None
            self._state = PlaybackState.STOPPED
            if self._mixer_initialized:
                quit_mixer()
                self._mixer_initialized = False

    # ── Internal helpers (must be called with _lock held) ───────────────

    def _set_state(self, new_state: PlaybackState) -> None:
        old_state = self._state
        self._state = new_state
        if old_state != new_state:
            self._emit(PlaybackEventType.STATE_CHANGED, new_state)

    def _emit(
        self,
        event_type: PlaybackEventType,
        state: PlaybackState,
        **kwargs: object,
    ) -> None:
        if self._on_event is not None:
            chunk_index = -1
            total_chunks = 0
            if self._session is not None:
                chunk_index = self._session.position
                total_chunks = self._session.total_chunks
            event = PlaybackEvent(
                event_type=event_type,
                state=state,
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                message=str(kwargs.get("message", "")),
            )
            try:
                self._on_event(event)
            except Exception:
                log.exception("Error in playback controller event callback")

    def _get_tts_settings(self) -> tuple[str, float, float]:
        """Return current (voice_id, speed, volume) for the TTS worker."""
        return self._voice_id, self._speed, self._volume

    def _init_mixer_if_needed(self) -> None:
        if not self._mixer_initialized:
            init_mixer()
            self._mixer_initialized = True

    def _start_playback(self) -> None:
        assert self._session is not None

        self._stop_event.clear()
        self._pause_event.clear()
        self._skip_event.clear()

        self._buffer = AudioBuffer()

        self._set_state(PlaybackState.BUFFERING)

        self._worker = TTSWorker(
            engine_manager=self._engine_manager,
            buffer=self._buffer,
            chunks=self._session.chunks,
            start_index=self._session.position,
            get_settings=self._get_tts_settings,
            stop_event=self._stop_event,
            skip_event=self._skip_event,
        )

        self._player = AudioPlayer(
            buffer=self._buffer,
            total_chunks=self._session.total_chunks,
            stop_event=self._stop_event,
            pause_event=self._pause_event,
            skip_event=self._skip_event,
            on_event=self._handle_player_event,
        )

        self._worker.start()
        self._player.start()

    def _handle_player_event(self, event: PlaybackEvent) -> None:
        """Forward player events to the controller callback, updating state.

        Called from the AudioPlayer thread — must NOT acquire _lock to avoid
        deadlock with skip/stop methods that hold _lock while joining threads.
        Single-field assignment is atomic under the GIL.
        """
        if event.event_type == PlaybackEventType.STATE_CHANGED:
            self._state = event.state
        if (
            event.event_type == PlaybackEventType.POSITION_CHANGED
            and self._session is not None
            and event.chunk_index >= 0
        ):
            self._session.jump_to(event.chunk_index)
        if self._on_event is not None:
            try:
                self._on_event(event)
            except Exception:
                log.exception("Error in playback controller event callback")

    def _resume_internal(self) -> None:
        self._pause_event.clear()
        self._set_state(PlaybackState.PLAYING)

    def _stop_internal(self) -> None:
        self._stop_event.set()
        stop_all_playback()

        # Don't join daemon threads — they'll exit shortly after seeing
        # the stop event. Joining on the main thread would freeze the UI
        # (worker may be blocked in a long TTS synthesis call).
        self._worker = None
        self._player = None

        if self._buffer is not None:
            self._buffer.reset()
            self._buffer = None

        self._set_state(PlaybackState.STOPPED)

    def _restart_from_position(self, position: int) -> None:
        """Stop current playback and restart from a new position.

        Signals old threads to stop and immediately starts new ones with
        fresh events. Old daemon threads will exit on their own after
        seeing their stop event. This avoids blocking the UI thread.
        """
        self._stop_event.set()
        stop_all_playback()

        was_paused = self._state == PlaybackState.PAUSED

        # Create fresh events so old threads (referencing old events)
        # don't interfere with the new playback cycle.
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._skip_event = threading.Event()

        if self._buffer is not None:
            self._buffer.reset()

        self._start_playback()
        if was_paused:
            self._pause_event.set()
            self._state = PlaybackState.PAUSED
