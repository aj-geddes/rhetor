"""Tests for EdgeTTSEngine — speed/volume conversion, mocked synthesis."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tts.base_engine import TTSEngineNotAvailableError, TTSSynthesisError
from tts.edge_engine import EdgeTTSEngine
from tts.models import AudioFormat


class TestSpeedConversion:
    def test_normal_speed(self) -> None:
        assert EdgeTTSEngine._speed_to_rate_string(1.0) == "+0%"

    def test_fast_speed(self) -> None:
        assert EdgeTTSEngine._speed_to_rate_string(1.25) == "+25%"

    def test_slow_speed(self) -> None:
        assert EdgeTTSEngine._speed_to_rate_string(0.7) == "-30%"

    def test_double_speed(self) -> None:
        assert EdgeTTSEngine._speed_to_rate_string(2.0) == "+100%"

    def test_half_speed(self) -> None:
        assert EdgeTTSEngine._speed_to_rate_string(0.5) == "-50%"


class TestVolumeConversion:
    def test_full_volume(self) -> None:
        assert EdgeTTSEngine._volume_to_string(1.0) == "+0%"

    def test_reduced_volume(self) -> None:
        assert EdgeTTSEngine._volume_to_string(0.8) == "-20%"

    def test_minimum_volume(self) -> None:
        assert EdgeTTSEngine._volume_to_string(0.0) == "-100%"


class TestEngineType:
    def test_engine_type(self) -> None:
        engine = EdgeTTSEngine()
        assert engine.engine_type == "edge"


class TestSynthesis:
    @patch("tts.edge_engine._EDGE_AVAILABLE", True)
    @patch("tts.edge_engine.edge_tts")
    def test_successful_synthesis(self, mock_edge_tts: MagicMock) -> None:
        """Test that synthesis returns an MP3 SynthesisResult."""
        mock_communicate = MagicMock()
        mock_edge_tts.Communicate.return_value = mock_communicate

        async def mock_stream() -> None:
            yield {"type": "audio", "data": b"\xff\xfb\x90\x00"}
            yield {"type": "audio", "data": b"\x00\x01\x02\x03"}
            yield {"type": "WordBoundary", "data": None}

        mock_communicate.stream = mock_stream

        engine = EdgeTTSEngine()
        result = engine.synthesize("Hello world", "en-US-JennyNeural")

        assert result.audio_format == AudioFormat.MP3
        assert result.sample_rate == 24000
        assert result.audio_data == b"\xff\xfb\x90\x00\x00\x01\x02\x03"

    @patch("tts.edge_engine._EDGE_AVAILABLE", True)
    @patch("tts.edge_engine.edge_tts")
    def test_empty_text_raises(self, mock_edge_tts: MagicMock) -> None:
        engine = EdgeTTSEngine()
        with pytest.raises(TTSSynthesisError, match="empty text"):
            engine.synthesize("  ", "en-US-JennyNeural")

    @patch("tts.edge_engine._EDGE_AVAILABLE", False)
    def test_unavailable_raises(self) -> None:
        engine = EdgeTTSEngine()
        with pytest.raises(TTSEngineNotAvailableError, match="not installed"):
            engine.synthesize("Hello", "en-US-JennyNeural")

    @patch("tts.edge_engine._EDGE_AVAILABLE", True)
    @patch("tts.edge_engine.edge_tts")
    def test_no_audio_data_raises(self, mock_edge_tts: MagicMock) -> None:
        """Edge returns no audio chunks."""
        mock_communicate = MagicMock()
        mock_edge_tts.Communicate.return_value = mock_communicate

        async def mock_stream() -> None:
            yield {"type": "WordBoundary", "data": None}

        mock_communicate.stream = mock_stream

        engine = EdgeTTSEngine()
        with pytest.raises(TTSSynthesisError, match="no audio data"):
            engine.synthesize("Hello", "en-US-JennyNeural")

    @patch("tts.edge_engine._EDGE_AVAILABLE", True)
    @patch("tts.edge_engine.edge_tts")
    def test_synthesis_exception_wrapped(self, mock_edge_tts: MagicMock) -> None:
        """Non-TTSSynthesisError exceptions are wrapped."""
        mock_edge_tts.Communicate.side_effect = RuntimeError("network down")

        engine = EdgeTTSEngine()
        with pytest.raises(TTSSynthesisError, match="Edge TTS synthesis failed"):
            engine.synthesize("Hello", "en-US-JennyNeural")


class TestAvailability:
    @patch("tts.edge_engine._EDGE_AVAILABLE", False)
    def test_not_available_without_library(self) -> None:
        engine = EdgeTTSEngine()
        assert engine.is_available is False

    @patch("tts.edge_engine._EDGE_AVAILABLE", True)
    @patch("tts.edge_engine.socket.create_connection")
    def test_available_with_connectivity(self, mock_socket: MagicMock) -> None:
        mock_conn = MagicMock()
        mock_socket.return_value = mock_conn
        engine = EdgeTTSEngine()
        assert engine.is_available is True
        mock_conn.close.assert_called_once()

    @patch("tts.edge_engine._EDGE_AVAILABLE", True)
    @patch("tts.edge_engine.socket.create_connection", side_effect=OSError("no network"))
    def test_not_available_without_connectivity(self, mock_socket: MagicMock) -> None:
        engine = EdgeTTSEngine()
        assert engine.is_available is False


class TestGetVoices:
    def test_get_voices_returns_edge_voices(self) -> None:
        engine = EdgeTTSEngine()
        voices = engine.get_voices()
        assert len(voices) == 8
        assert all(v.engine == "edge" for v in voices)
