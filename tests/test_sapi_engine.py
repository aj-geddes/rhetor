"""Tests for SapiTTSEngine — mocked pyttsx3, temp file synthesis, voice discovery."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tts.base_engine import TTSEngineNotAvailableError, TTSSynthesisError
from tts.models import AudioFormat
from tts.sapi_engine import SapiTTSEngine


class TestEngineType:
    def test_engine_type(self) -> None:
        engine = SapiTTSEngine()
        assert engine.engine_type == "sapi"


class TestSynthesis:
    @patch("tts.sapi_engine._PYTTSX3_AVAILABLE", True)
    @patch("tts.sapi_engine.pyttsx3")
    def test_successful_synthesis(self, mock_pyttsx3: MagicMock, tmp_path: MagicMock) -> None:
        """Test that synthesis writes to temp file and returns WAV bytes."""
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine

        # Make save_to_file write actual WAV data to the temp file
        def fake_save_to_file(text: str, path: str) -> None:
            import struct
            import wave

            with wave.open(path, "wb") as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(22050)
                f.writeframes(struct.pack("<hh", 0, 100))

        mock_engine.save_to_file.side_effect = fake_save_to_file

        engine = SapiTTSEngine()
        result = engine.synthesize("Hello world", "voice-id", speed=1.0, volume=0.8)

        assert result.audio_format == AudioFormat.WAV
        assert result.sample_rate == 22050
        assert len(result.audio_data) > 0
        mock_engine.runAndWait.assert_called_once()

    @patch("tts.sapi_engine._PYTTSX3_AVAILABLE", True)
    @patch("tts.sapi_engine.pyttsx3")
    def test_speed_set_correctly(self, mock_pyttsx3: MagicMock) -> None:
        """Speed should be SAPI_BASE_WPM * speed multiplier."""
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine

        def fake_save_to_file(text: str, path: str) -> None:
            import struct
            import wave

            with wave.open(path, "wb") as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(22050)
                f.writeframes(struct.pack("<h", 0))

        mock_engine.save_to_file.side_effect = fake_save_to_file

        engine = SapiTTSEngine()
        engine.synthesize("Hello", "voice-id", speed=1.5, volume=1.0)

        # SAPI_BASE_WPM (200) * 1.5 = 300
        set_calls = mock_engine.setProperty.call_args_list
        rate_call = [c for c in set_calls if c[0][0] == "rate"]
        assert rate_call[0][0][1] == 300

    @patch("tts.sapi_engine._PYTTSX3_AVAILABLE", True)
    @patch("tts.sapi_engine.pyttsx3")
    def test_volume_set_correctly(self, mock_pyttsx3: MagicMock) -> None:
        """Volume should be passed directly to pyttsx3."""
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine

        def fake_save_to_file(text: str, path: str) -> None:
            import struct
            import wave

            with wave.open(path, "wb") as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(22050)
                f.writeframes(struct.pack("<h", 0))

        mock_engine.save_to_file.side_effect = fake_save_to_file

        engine = SapiTTSEngine()
        engine.synthesize("Hello", "voice-id", speed=1.0, volume=0.75)

        set_calls = mock_engine.setProperty.call_args_list
        volume_call = [c for c in set_calls if c[0][0] == "volume"]
        assert volume_call[0][0][1] == 0.75

    @patch("tts.sapi_engine._PYTTSX3_AVAILABLE", True)
    def test_empty_text_raises(self) -> None:
        engine = SapiTTSEngine()
        with pytest.raises(TTSSynthesisError, match="empty text"):
            engine.synthesize("  ", "voice-id")

    @patch("tts.sapi_engine._PYTTSX3_AVAILABLE", False)
    def test_unavailable_raises(self) -> None:
        engine = SapiTTSEngine()
        with pytest.raises(TTSEngineNotAvailableError, match="not installed"):
            engine.synthesize("Hello", "voice-id")


class TestVoiceDiscovery:
    @patch("tts.sapi_engine._PYTTSX3_AVAILABLE", True)
    @patch("tts.sapi_engine.pyttsx3")
    def test_get_voices(self, mock_pyttsx3: MagicMock) -> None:
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine

        mock_voice1 = MagicMock()
        mock_voice1.id = "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\David"
        mock_voice1.name = "Microsoft David"

        mock_voice2 = MagicMock()
        mock_voice2.id = "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\Zira"
        mock_voice2.name = "Microsoft Zira"

        mock_engine.getProperty.return_value = [mock_voice1, mock_voice2]

        engine = SapiTTSEngine()
        voices = engine.get_voices()

        assert len(voices) == 2
        assert voices[0].voice_id == "sapi-david"
        assert voices[0].engine == "sapi"
        assert voices[0].engine_voice_id == mock_voice1.id
        assert voices[1].voice_id == "sapi-zira"

    @patch("tts.sapi_engine._PYTTSX3_AVAILABLE", True)
    @patch("tts.sapi_engine.pyttsx3")
    def test_get_voices_init_failure(self, mock_pyttsx3: MagicMock) -> None:
        mock_pyttsx3.init.side_effect = RuntimeError("COM error")
        engine = SapiTTSEngine()
        assert engine.get_voices() == []


class TestAvailability:
    @patch("tts.sapi_engine._PYTTSX3_AVAILABLE", False)
    def test_not_available_without_library(self) -> None:
        engine = SapiTTSEngine()
        assert engine.is_available is False

    @patch("tts.sapi_engine._PYTTSX3_AVAILABLE", True)
    @patch("tts.sapi_engine.pyttsx3")
    def test_available_with_library(self, mock_pyttsx3: MagicMock) -> None:
        mock_pyttsx3.init.return_value = MagicMock()
        engine = SapiTTSEngine()
        assert engine.is_available is True

    @patch("tts.sapi_engine._PYTTSX3_AVAILABLE", True)
    @patch("tts.sapi_engine.pyttsx3")
    def test_not_available_on_init_failure(self, mock_pyttsx3: MagicMock) -> None:
        mock_pyttsx3.init.side_effect = RuntimeError("No SAPI")
        engine = SapiTTSEngine()
        assert engine.is_available is False


class TestLazyInit:
    @patch("tts.sapi_engine._PYTTSX3_AVAILABLE", True)
    @patch("tts.sapi_engine.pyttsx3")
    def test_engine_initialized_once(self, mock_pyttsx3: MagicMock) -> None:
        """pyttsx3.init() should be called only once across multiple operations."""
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine
        mock_engine.getProperty.return_value = []

        engine = SapiTTSEngine()
        engine.get_voices()
        engine.get_voices()

        assert mock_pyttsx3.init.call_count == 1
