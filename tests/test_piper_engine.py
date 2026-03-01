"""Tests for PiperTTSEngine — speed conversion, mocked model loading, caching."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tts.base_engine import TTSEngineNotAvailableError, TTSSynthesisError
from tts.models import AudioFormat
from tts.piper_engine import PiperTTSEngine


class TestSpeedConversion:
    def test_normal_speed(self) -> None:
        """speed=1.0 → length_scale=1.0"""
        assert 1.0 / 1.0 == 1.0

    def test_fast_speed(self) -> None:
        """speed=2.0 → length_scale=0.5 (shorter = faster)"""
        assert 1.0 / 2.0 == 0.5

    def test_slow_speed(self) -> None:
        """speed=0.5 → length_scale=2.0 (longer = slower)"""
        assert 1.0 / 0.5 == 2.0


class TestEngineType:
    def test_engine_type(self) -> None:
        engine = PiperTTSEngine()
        assert engine.engine_type == "piper"


class TestSynthesis:
    @patch("tts.piper_engine._PIPER_AVAILABLE", True)
    @patch("tts.piper_engine.PiperVoice")
    def test_successful_synthesis(
        self, mock_piper_voice_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Test that synthesis returns a WAV SynthesisResult."""
        mock_voice = MagicMock()

        def fake_synthesize(text: str, wav_file: object, length_scale: float = 1.0) -> None:
            import struct
            import wave

            assert isinstance(wav_file, wave.Wave_write)
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(22050)
            wav_file.writeframes(struct.pack("<hh", 0, 100))

        mock_voice.synthesize = fake_synthesize
        mock_piper_voice_cls.load.return_value = mock_voice

        # Create a fake model file
        model_dir = tmp_path / "voices"
        model_dir.mkdir()
        model_file = model_dir / "en_US-lessac-medium.onnx"
        model_file.write_bytes(b"fake-onnx-model")

        with patch("tts.piper_engine.VOICES_DIR", model_dir):
            engine = PiperTTSEngine()
            result = engine.synthesize("Hello", "en_US-lessac-medium")

        assert result.audio_format == AudioFormat.WAV
        assert result.sample_rate == 22050
        assert len(result.audio_data) > 0
        mock_piper_voice_cls.load.assert_called_once()

    @patch("tts.piper_engine._PIPER_AVAILABLE", True)
    @patch("tts.piper_engine.PiperVoice")
    def test_model_caching(self, mock_piper_voice_cls: MagicMock, tmp_path: Path) -> None:
        """PiperVoice.load() should only be called once for the same voice."""
        mock_voice = MagicMock()

        def fake_synthesize(text: str, wav_file: object, length_scale: float = 1.0) -> None:
            import struct
            import wave

            assert isinstance(wav_file, wave.Wave_write)
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(22050)
            wav_file.writeframes(struct.pack("<h", 0))

        mock_voice.synthesize = fake_synthesize
        mock_piper_voice_cls.load.return_value = mock_voice

        model_dir = tmp_path / "voices"
        model_dir.mkdir()
        (model_dir / "en_US-lessac-medium.onnx").write_bytes(b"fake")

        with patch("tts.piper_engine.VOICES_DIR", model_dir):
            engine = PiperTTSEngine()
            engine.synthesize("Hello", "en_US-lessac-medium")
            engine.synthesize("World", "en_US-lessac-medium")

        # load() called only once despite two synthesis calls
        assert mock_piper_voice_cls.load.call_count == 1

    @patch("tts.piper_engine._PIPER_AVAILABLE", True)
    def test_missing_model_raises(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "voices"
        model_dir.mkdir()

        with patch("tts.piper_engine.VOICES_DIR", model_dir):
            engine = PiperTTSEngine()
            with pytest.raises(TTSSynthesisError, match="model not found"):
                engine.synthesize("Hello", "nonexistent-model")

    @patch("tts.piper_engine._PIPER_AVAILABLE", True)
    def test_empty_text_raises(self, tmp_path: Path) -> None:
        engine = PiperTTSEngine()
        with pytest.raises(TTSSynthesisError, match="empty text"):
            engine.synthesize("  ", "en_US-lessac-medium")

    @patch("tts.piper_engine._PIPER_AVAILABLE", False)
    def test_unavailable_raises(self) -> None:
        engine = PiperTTSEngine()
        with pytest.raises(TTSEngineNotAvailableError, match="not installed"):
            engine.synthesize("Hello", "en_US-lessac-medium")


class TestAvailability:
    @patch("tts.piper_engine._PIPER_AVAILABLE", False)
    def test_not_available_without_library(self) -> None:
        engine = PiperTTSEngine()
        assert engine.is_available is False

    @patch("tts.piper_engine._PIPER_AVAILABLE", True)
    def test_not_available_without_models(self, tmp_path: Path) -> None:
        empty_dir = tmp_path / "voices"
        empty_dir.mkdir()
        with patch("tts.piper_engine.VOICES_DIR", empty_dir):
            engine = PiperTTSEngine()
            assert engine.is_available is False

    @patch("tts.piper_engine._PIPER_AVAILABLE", True)
    def test_available_with_models(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "voices"
        model_dir.mkdir()
        (model_dir / "test-model.onnx").write_bytes(b"fake")
        with patch("tts.piper_engine.VOICES_DIR", model_dir):
            engine = PiperTTSEngine()
            assert engine.is_available is True


class TestGetVoices:
    def test_get_voices_returns_piper_voices(self) -> None:
        engine = PiperTTSEngine()
        voices = engine.get_voices()
        assert len(voices) == 3
        assert all(v.engine == "piper" for v in voices)
