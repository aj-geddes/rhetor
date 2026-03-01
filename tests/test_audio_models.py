"""Tests for audio pipeline data models."""

from __future__ import annotations

import dataclasses

import pytest

from audio.models import (
    AudioChunk,
    AudioError,
    AudioPlaybackError,
    AudioPlayerNotAvailableError,
    PlaybackEvent,
    PlaybackEventType,
    PlaybackState,
)

# ── PlaybackState ───────────────────────────────────────────────────────────


class TestPlaybackState:
    def test_variants_exist(self) -> None:
        assert PlaybackState.IDLE is not None
        assert PlaybackState.BUFFERING is not None
        assert PlaybackState.PLAYING is not None
        assert PlaybackState.PAUSED is not None
        assert PlaybackState.STOPPED is not None
        assert PlaybackState.FINISHED is not None

    def test_variants_are_distinct(self) -> None:
        states = list(PlaybackState)
        for i, a in enumerate(states):
            for b in states[i + 1 :]:
                assert a != b

    def test_member_count(self) -> None:
        assert len(PlaybackState) == 6


# ── PlaybackEventType ──────────────────────────────────────────────────────


class TestPlaybackEventType:
    def test_variants_exist(self) -> None:
        assert PlaybackEventType.STATE_CHANGED is not None
        assert PlaybackEventType.CHUNK_STARTED is not None
        assert PlaybackEventType.CHUNK_FINISHED is not None
        assert PlaybackEventType.POSITION_CHANGED is not None
        assert PlaybackEventType.ERROR is not None

    def test_member_count(self) -> None:
        assert len(PlaybackEventType) == 5


# ── AudioChunk ─────────────────────────────────────────────────────────────


class TestAudioChunk:
    def test_create(self) -> None:
        chunk = AudioChunk(
            audio_data=b"\x00\x01",
            chunk_index=0,
            text="Hello world.",
            format="mp3",
        )
        assert chunk.audio_data == b"\x00\x01"
        assert chunk.chunk_index == 0
        assert chunk.text == "Hello world."
        assert chunk.format == "mp3"

    def test_frozen(self) -> None:
        chunk = AudioChunk(audio_data=b"data", chunk_index=0, text="Hi.", format="wav")
        with pytest.raises(dataclasses.FrozenInstanceError):
            chunk.chunk_index = 1  # type: ignore[misc]

    def test_has_slots(self) -> None:
        assert hasattr(AudioChunk, "__slots__")

    def test_equality(self) -> None:
        a = AudioChunk(audio_data=b"x", chunk_index=0, text="t", format="mp3")
        b = AudioChunk(audio_data=b"x", chunk_index=0, text="t", format="mp3")
        assert a == b

    def test_inequality(self) -> None:
        a = AudioChunk(audio_data=b"x", chunk_index=0, text="t", format="mp3")
        b = AudioChunk(audio_data=b"y", chunk_index=0, text="t", format="mp3")
        assert a != b


# ── PlaybackEvent ──────────────────────────────────────────────────────────


class TestPlaybackEvent:
    def test_create_with_required_fields(self) -> None:
        event = PlaybackEvent(
            event_type=PlaybackEventType.STATE_CHANGED,
            state=PlaybackState.PLAYING,
        )
        assert event.event_type == PlaybackEventType.STATE_CHANGED
        assert event.state == PlaybackState.PLAYING

    def test_defaults(self) -> None:
        event = PlaybackEvent(
            event_type=PlaybackEventType.CHUNK_STARTED,
            state=PlaybackState.PLAYING,
        )
        assert event.chunk_index == -1
        assert event.total_chunks == 0
        assert event.message == ""

    def test_with_all_fields(self) -> None:
        event = PlaybackEvent(
            event_type=PlaybackEventType.ERROR,
            state=PlaybackState.STOPPED,
            chunk_index=5,
            total_chunks=20,
            message="Playback device lost",
        )
        assert event.chunk_index == 5
        assert event.total_chunks == 20
        assert event.message == "Playback device lost"

    def test_frozen(self) -> None:
        event = PlaybackEvent(
            event_type=PlaybackEventType.STATE_CHANGED,
            state=PlaybackState.IDLE,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            event.state = PlaybackState.PLAYING  # type: ignore[misc]

    def test_has_slots(self) -> None:
        assert hasattr(PlaybackEvent, "__slots__")


# ── Exceptions ─────────────────────────────────────────────────────────────


class TestExceptions:
    def test_audio_error_is_exception(self) -> None:
        assert issubclass(AudioError, Exception)

    def test_player_not_available_inherits(self) -> None:
        assert issubclass(AudioPlayerNotAvailableError, AudioError)

    def test_playback_error_inherits(self) -> None:
        assert issubclass(AudioPlaybackError, AudioError)

    def test_audio_error_message(self) -> None:
        err = AudioError("something went wrong")
        assert str(err) == "something went wrong"

    def test_player_not_available_message(self) -> None:
        err = AudioPlayerNotAvailableError("pygame not installed")
        assert str(err) == "pygame not installed"

    def test_playback_error_message(self) -> None:
        err = AudioPlaybackError("corrupt audio")
        assert str(err) == "corrupt audio"

    def test_can_catch_subclass_as_base(self) -> None:
        with pytest.raises(AudioError):
            raise AudioPlaybackError("test")
