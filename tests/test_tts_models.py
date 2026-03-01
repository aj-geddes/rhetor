"""Tests for TTS data models — AudioFormat, SynthesisResult, VoiceInfo."""

from __future__ import annotations

import dataclasses

import pytest

from tts.models import AudioFormat, SynthesisResult, VoiceInfo

# ── AudioFormat ──────────────────────────────────────────────────────────────


class TestAudioFormat:
    def test_variants_exist(self) -> None:
        assert AudioFormat.MP3 is not None
        assert AudioFormat.WAV is not None
        assert AudioFormat.PCM_RAW is not None

    def test_variants_are_distinct(self) -> None:
        assert AudioFormat.MP3 != AudioFormat.WAV
        assert AudioFormat.WAV != AudioFormat.PCM_RAW
        assert AudioFormat.MP3 != AudioFormat.PCM_RAW

    def test_member_count(self) -> None:
        assert len(AudioFormat) == 3


# ── SynthesisResult ──────────────────────────────────────────────────────────


class TestSynthesisResult:
    def test_create_with_required_fields(self) -> None:
        result = SynthesisResult(
            audio_data=b"\x00\x01\x02",
            audio_format=AudioFormat.MP3,
            sample_rate=24000,
        )
        assert result.audio_data == b"\x00\x01\x02"
        assert result.audio_format == AudioFormat.MP3
        assert result.sample_rate == 24000

    def test_defaults(self) -> None:
        result = SynthesisResult(
            audio_data=b"data",
            audio_format=AudioFormat.WAV,
            sample_rate=22050,
        )
        assert result.sample_width == 2
        assert result.channels == 1

    def test_frozen(self) -> None:
        result = SynthesisResult(
            audio_data=b"data",
            audio_format=AudioFormat.WAV,
            sample_rate=22050,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.sample_rate = 44100  # type: ignore[misc]

    def test_has_slots(self) -> None:
        assert hasattr(SynthesisResult, "__slots__")

    def test_equality(self) -> None:
        a = SynthesisResult(audio_data=b"x", audio_format=AudioFormat.MP3, sample_rate=24000)
        b = SynthesisResult(audio_data=b"x", audio_format=AudioFormat.MP3, sample_rate=24000)
        assert a == b


# ── VoiceInfo ────────────────────────────────────────────────────────────────


class TestVoiceInfo:
    def test_create_minimal(self) -> None:
        voice = VoiceInfo(
            voice_id="test-voice",
            name="Test Voice",
            engine="edge",
            engine_voice_id="en-US-TestNeural",
        )
        assert voice.voice_id == "test-voice"
        assert voice.name == "Test Voice"
        assert voice.engine == "edge"
        assert voice.engine_voice_id == "en-US-TestNeural"

    def test_defaults(self) -> None:
        voice = VoiceInfo(
            voice_id="v1",
            name="V1",
            engine="edge",
            engine_voice_id="en-US-V1Neural",
        )
        assert voice.gender == ""
        assert voice.language == "en"
        assert voice.accent == ""
        assert voice.description == ""
        assert voice.requires_internet is False
        assert voice.preview_text == "Hello, I'm ready to read your documents."

    def test_frozen(self) -> None:
        voice = VoiceInfo(
            voice_id="v1",
            name="V1",
            engine="edge",
            engine_voice_id="en-US-V1Neural",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            voice.name = "Changed"  # type: ignore[misc]

    def test_has_slots(self) -> None:
        assert hasattr(VoiceInfo, "__slots__")

    def test_with_all_fields(self) -> None:
        voice = VoiceInfo(
            voice_id="jenny-us",
            name="Jenny (US)",
            engine="edge",
            engine_voice_id="en-US-JennyNeural",
            gender="female",
            language="en",
            accent="US",
            description="Friendly voice",
            requires_internet=True,
            preview_text="Hello!",
        )
        assert voice.gender == "female"
        assert voice.requires_internet is True
        assert voice.preview_text == "Hello!"
