"""AudioBuffer — bounded queue wrapper for decoupling TTS synthesis from playback."""

from __future__ import annotations

import queue
import threading

from audio.models import AudioChunk
from constants import AUDIO_BUFFER_CAPACITY


class AudioBuffer:
    """Thread-safe bounded buffer for AudioChunk objects.

    Wraps a ``queue.Queue`` with a completion signal so the consumer
    knows when no more chunks will arrive.
    """

    def __init__(self, capacity: int = AUDIO_BUFFER_CAPACITY) -> None:
        self._queue: queue.Queue[AudioChunk] = queue.Queue(maxsize=capacity)
        self._complete = threading.Event()
        self._capacity = capacity

    @property
    def capacity(self) -> int:
        """Maximum number of chunks the buffer can hold."""
        return self._capacity

    @property
    def is_complete(self) -> bool:
        """True when the producer has signalled no more chunks will arrive."""
        return self._complete.is_set()

    @property
    def is_empty(self) -> bool:
        """True when the buffer has no chunks ready for consumption."""
        return self._queue.empty()

    @property
    def size(self) -> int:
        """Approximate number of chunks currently in the buffer."""
        return self._queue.qsize()

    def put(self, chunk: AudioChunk, timeout: float | None = None) -> bool:
        """Add a chunk to the buffer.

        Args:
            chunk: The audio chunk to enqueue.
            timeout: Seconds to wait if buffer is full. None = block forever.

        Returns:
            True if the chunk was added, False if the buffer was full and timed out.
        """
        try:
            self._queue.put(chunk, block=True, timeout=timeout)
            return True
        except queue.Full:
            return False

    def get(self, timeout: float | None = None) -> AudioChunk | None:
        """Remove and return the next chunk from the buffer.

        Args:
            timeout: Seconds to wait if buffer is empty. None = block forever.

        Returns:
            The next AudioChunk, or None if the buffer is empty and timed out.
        """
        try:
            return self._queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return None

    def clear(self) -> int:
        """Drain all pending chunks from the buffer.

        Returns:
            The number of chunks discarded.
        """
        count = 0
        while True:
            try:
                self._queue.get_nowait()
                count += 1
            except queue.Empty:
                break
        return count

    def signal_complete(self) -> None:
        """Signal that no more chunks will be added to the buffer."""
        self._complete.set()

    def reset(self) -> None:
        """Clear the buffer and reset the completion signal for reuse."""
        self.clear()
        self._complete.clear()
