"""Tests for AudioBuffer — bounded queue wrapper."""

from __future__ import annotations

import threading
import time

from audio.buffer import AudioBuffer
from audio.models import AudioChunk


def _make_chunk(index: int = 0) -> AudioChunk:
    return AudioChunk(audio_data=b"\x00", chunk_index=index, text="hi", format="wav")


# ── Basic operations ────────────────────────────────────────────────────────


class TestAudioBufferBasic:
    def test_default_capacity(self) -> None:
        buf = AudioBuffer()
        assert buf.capacity == 3

    def test_custom_capacity(self) -> None:
        buf = AudioBuffer(capacity=5)
        assert buf.capacity == 5

    def test_starts_empty(self) -> None:
        buf = AudioBuffer()
        assert buf.is_empty
        assert buf.size == 0

    def test_put_and_get(self) -> None:
        buf = AudioBuffer()
        chunk = _make_chunk(0)
        assert buf.put(chunk) is True
        assert buf.size == 1
        assert not buf.is_empty
        result = buf.get(timeout=1.0)
        assert result == chunk
        assert buf.is_empty

    def test_fifo_order(self) -> None:
        buf = AudioBuffer(capacity=3)
        for i in range(3):
            buf.put(_make_chunk(i))
        for i in range(3):
            chunk = buf.get(timeout=1.0)
            assert chunk is not None
            assert chunk.chunk_index == i

    def test_get_returns_none_on_timeout(self) -> None:
        buf = AudioBuffer()
        result = buf.get(timeout=0.05)
        assert result is None

    def test_put_returns_false_on_full_timeout(self) -> None:
        buf = AudioBuffer(capacity=1)
        buf.put(_make_chunk(0))
        result = buf.put(_make_chunk(1), timeout=0.05)
        assert result is False


# ── Clear ───────────────────────────────────────────────────────────────────


class TestAudioBufferClear:
    def test_clear_empty(self) -> None:
        buf = AudioBuffer()
        assert buf.clear() == 0

    def test_clear_returns_count(self) -> None:
        buf = AudioBuffer(capacity=3)
        for i in range(3):
            buf.put(_make_chunk(i))
        assert buf.clear() == 3
        assert buf.is_empty

    def test_clear_allows_new_puts(self) -> None:
        buf = AudioBuffer(capacity=1)
        buf.put(_make_chunk(0))
        buf.clear()
        assert buf.put(_make_chunk(1), timeout=0.1) is True


# ── Completion signal ───────────────────────────────────────────────────────


class TestAudioBufferCompletion:
    def test_not_complete_initially(self) -> None:
        buf = AudioBuffer()
        assert not buf.is_complete

    def test_signal_complete(self) -> None:
        buf = AudioBuffer()
        buf.signal_complete()
        assert buf.is_complete

    def test_reset_clears_completion(self) -> None:
        buf = AudioBuffer()
        buf.signal_complete()
        buf.reset()
        assert not buf.is_complete

    def test_reset_clears_data(self) -> None:
        buf = AudioBuffer(capacity=3)
        for i in range(3):
            buf.put(_make_chunk(i))
        buf.signal_complete()
        buf.reset()
        assert buf.is_empty
        assert not buf.is_complete


# ── Thread safety ───────────────────────────────────────────────────────────


class TestAudioBufferThreadSafety:
    def test_concurrent_put_get(self) -> None:
        buf = AudioBuffer(capacity=2)
        results: list[AudioChunk] = []
        errors: list[Exception] = []

        def producer() -> None:
            try:
                for i in range(10):
                    buf.put(_make_chunk(i), timeout=2.0)
                buf.signal_complete()
            except Exception as exc:
                errors.append(exc)

        def consumer() -> None:
            try:
                while True:
                    chunk = buf.get(timeout=0.5)
                    if chunk is not None:
                        results.append(chunk)
                    elif buf.is_complete:
                        break
            except Exception as exc:
                errors.append(exc)

        t_prod = threading.Thread(target=producer)
        t_cons = threading.Thread(target=consumer)
        t_prod.start()
        t_cons.start()
        t_prod.join(timeout=5.0)
        t_cons.join(timeout=5.0)

        assert not errors
        assert len(results) == 10
        indices = [c.chunk_index for c in results]
        assert indices == list(range(10))

    def test_blocking_put_unblocked_by_get(self) -> None:
        buf = AudioBuffer(capacity=1)
        buf.put(_make_chunk(0))
        put_done = threading.Event()

        def delayed_get() -> None:
            time.sleep(0.1)
            buf.get(timeout=1.0)

        def blocking_put() -> None:
            buf.put(_make_chunk(1), timeout=2.0)
            put_done.set()

        t1 = threading.Thread(target=delayed_get)
        t2 = threading.Thread(target=blocking_put)
        t1.start()
        t2.start()
        t1.join(timeout=3.0)
        t2.join(timeout=3.0)
        assert put_done.is_set()
