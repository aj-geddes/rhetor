"""Tests for EngineManager — selection, failover, voice resolution."""

from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from tts.base_engine import TTSEngineNotAvailableError, TTSSynthesisError
from tts.engine_manager import EngineManager
from tts.models import AudioFormat, SynthesisResult


def _make_mock_engine(
    engine_type: str,
    available: bool = True,
    voices: list[object] | None = None,
) -> MagicMock:
    """Create a mock TTS engine."""
    engine = MagicMock()
    type(engine).engine_type = PropertyMock(return_value=engine_type)
    type(engine).is_available = PropertyMock(return_value=available)
    engine.get_voices.return_value = voices or []
    return engine


def _make_result(fmt: AudioFormat = AudioFormat.MP3) -> SynthesisResult:
    return SynthesisResult(
        audio_data=b"\x00\x01",
        audio_format=fmt,
        sample_rate=24000,
    )


class TestInitialize:
    @patch("tts.engine_manager.SapiTTSEngine")
    @patch("tts.engine_manager.PiperTTSEngine")
    @patch("tts.engine_manager.EdgeTTSEngine")
    def test_auto_selects_edge_when_online(
        self,
        mock_edge_cls: MagicMock,
        mock_piper_cls: MagicMock,
        mock_sapi_cls: MagicMock,
    ) -> None:
        mock_edge_cls.return_value = _make_mock_engine("edge", available=True)
        mock_piper_cls.return_value = _make_mock_engine("piper", available=True)
        mock_sapi_cls.return_value = _make_mock_engine("sapi", available=True)

        mgr = EngineManager()
        mgr.initialize()
        assert mgr.active_engine == "edge"

    @patch("tts.engine_manager.SapiTTSEngine")
    @patch("tts.engine_manager.PiperTTSEngine")
    @patch("tts.engine_manager.EdgeTTSEngine")
    def test_auto_selects_piper_when_edge_unavailable(
        self,
        mock_edge_cls: MagicMock,
        mock_piper_cls: MagicMock,
        mock_sapi_cls: MagicMock,
    ) -> None:
        mock_edge_cls.return_value = _make_mock_engine("edge", available=False)
        mock_piper_cls.return_value = _make_mock_engine("piper", available=True)
        mock_sapi_cls.return_value = _make_mock_engine("sapi", available=True)

        mgr = EngineManager()
        mgr.initialize()
        assert mgr.active_engine == "piper"

    @patch("tts.engine_manager.SapiTTSEngine")
    @patch("tts.engine_manager.PiperTTSEngine")
    @patch("tts.engine_manager.EdgeTTSEngine")
    def test_auto_selects_sapi_as_last_resort(
        self,
        mock_edge_cls: MagicMock,
        mock_piper_cls: MagicMock,
        mock_sapi_cls: MagicMock,
    ) -> None:
        mock_edge_cls.return_value = _make_mock_engine("edge", available=False)
        mock_piper_cls.return_value = _make_mock_engine("piper", available=False)
        mock_sapi_cls.return_value = _make_mock_engine("sapi", available=True)

        mgr = EngineManager()
        mgr.initialize()
        assert mgr.active_engine == "sapi"

    @patch("tts.engine_manager.SapiTTSEngine")
    @patch("tts.engine_manager.PiperTTSEngine")
    @patch("tts.engine_manager.EdgeTTSEngine")
    def test_no_engines_available_raises(
        self,
        mock_edge_cls: MagicMock,
        mock_piper_cls: MagicMock,
        mock_sapi_cls: MagicMock,
    ) -> None:
        mock_edge_cls.return_value = _make_mock_engine("edge", available=False)
        mock_piper_cls.return_value = _make_mock_engine("piper", available=False)
        mock_sapi_cls.return_value = _make_mock_engine("sapi", available=False)

        mgr = EngineManager()
        with pytest.raises(TTSEngineNotAvailableError, match="No TTS engine"):
            mgr.initialize()

    @patch("tts.engine_manager.SapiTTSEngine")
    @patch("tts.engine_manager.PiperTTSEngine")
    @patch("tts.engine_manager.EdgeTTSEngine")
    def test_force_offline_skips_edge(
        self,
        mock_edge_cls: MagicMock,
        mock_piper_cls: MagicMock,
        mock_sapi_cls: MagicMock,
    ) -> None:
        mock_edge_cls.return_value = _make_mock_engine("edge", available=True)
        mock_piper_cls.return_value = _make_mock_engine("piper", available=True)
        mock_sapi_cls.return_value = _make_mock_engine("sapi", available=True)

        mgr = EngineManager()
        mgr.initialize(force_offline=True)
        assert mgr.active_engine == "piper"

    @patch("tts.engine_manager.SapiTTSEngine")
    @patch("tts.engine_manager.PiperTTSEngine")
    @patch("tts.engine_manager.EdgeTTSEngine")
    def test_preferred_engine_honored(
        self,
        mock_edge_cls: MagicMock,
        mock_piper_cls: MagicMock,
        mock_sapi_cls: MagicMock,
    ) -> None:
        mock_edge_cls.return_value = _make_mock_engine("edge", available=True)
        mock_piper_cls.return_value = _make_mock_engine("piper", available=True)
        mock_sapi_cls.return_value = _make_mock_engine("sapi", available=True)

        mgr = EngineManager()
        mgr.initialize(preferred_engine="piper")
        assert mgr.active_engine == "piper"

    @patch("tts.engine_manager.SapiTTSEngine")
    @patch("tts.engine_manager.PiperTTSEngine")
    @patch("tts.engine_manager.EdgeTTSEngine")
    def test_preferred_engine_unavailable_falls_back(
        self,
        mock_edge_cls: MagicMock,
        mock_piper_cls: MagicMock,
        mock_sapi_cls: MagicMock,
    ) -> None:
        mock_edge_cls.return_value = _make_mock_engine("edge", available=True)
        mock_piper_cls.return_value = _make_mock_engine("piper", available=False)
        mock_sapi_cls.return_value = _make_mock_engine("sapi", available=True)

        mgr = EngineManager()
        mgr.initialize(preferred_engine="piper")
        assert mgr.active_engine == "edge"


class TestSynthesize:
    @patch("tts.engine_manager.SapiTTSEngine")
    @patch("tts.engine_manager.PiperTTSEngine")
    @patch("tts.engine_manager.EdgeTTSEngine")
    def test_successful_synthesis(
        self,
        mock_edge_cls: MagicMock,
        mock_piper_cls: MagicMock,
        mock_sapi_cls: MagicMock,
    ) -> None:
        edge = _make_mock_engine("edge", available=True)
        expected = _make_result(AudioFormat.MP3)
        edge.synthesize.return_value = expected
        mock_edge_cls.return_value = edge
        mock_piper_cls.return_value = _make_mock_engine("piper", available=False)
        mock_sapi_cls.return_value = _make_mock_engine("sapi", available=False)

        mgr = EngineManager()
        mgr.initialize()
        result = mgr.synthesize("Hello", "jenny-us")

        assert result == expected
        # Should resolve jenny-us → en-US-JennyNeural
        edge.synthesize.assert_called_once_with(
            "Hello", "en-US-JennyNeural", 1.0, 1.0
        )

    @patch("tts.engine_manager.SapiTTSEngine")
    @patch("tts.engine_manager.PiperTTSEngine")
    @patch("tts.engine_manager.EdgeTTSEngine")
    def test_failover_on_synthesis_error(
        self,
        mock_edge_cls: MagicMock,
        mock_piper_cls: MagicMock,
        mock_sapi_cls: MagicMock,
    ) -> None:
        edge = _make_mock_engine("edge", available=True)
        edge.synthesize.side_effect = TTSSynthesisError("network error")
        mock_edge_cls.return_value = edge

        piper = _make_mock_engine("piper", available=True)
        piper_result = _make_result(AudioFormat.WAV)
        piper.synthesize.return_value = piper_result
        mock_piper_cls.return_value = piper

        mock_sapi_cls.return_value = _make_mock_engine("sapi", available=False)

        mgr = EngineManager()
        mgr.initialize()
        assert mgr.active_engine == "edge"

        result = mgr.synthesize("Hello", "jenny-us")
        assert result == piper_result
        assert mgr.active_engine == "piper"

    @patch("tts.engine_manager.SapiTTSEngine")
    @patch("tts.engine_manager.PiperTTSEngine")
    @patch("tts.engine_manager.EdgeTTSEngine")
    def test_all_engines_fail_raises(
        self,
        mock_edge_cls: MagicMock,
        mock_piper_cls: MagicMock,
        mock_sapi_cls: MagicMock,
    ) -> None:
        edge = _make_mock_engine("edge", available=True)
        edge.synthesize.side_effect = TTSSynthesisError("fail")
        mock_edge_cls.return_value = edge

        piper = _make_mock_engine("piper", available=True)
        piper.synthesize.side_effect = TTSSynthesisError("fail")
        mock_piper_cls.return_value = piper

        sapi = _make_mock_engine("sapi", available=True)
        sapi.synthesize.side_effect = TTSSynthesisError("fail")
        mock_sapi_cls.return_value = sapi

        mgr = EngineManager()
        mgr.initialize()

        with pytest.raises(TTSSynthesisError, match="All TTS engines failed"):
            mgr.synthesize("Hello", "jenny-us")

    def test_synthesize_without_init_raises(self) -> None:
        mgr = EngineManager()
        with pytest.raises(TTSEngineNotAvailableError, match="not initialized"):
            mgr.synthesize("Hello", "jenny-us")


class TestVoiceResolution:
    @patch("tts.engine_manager.SapiTTSEngine")
    @patch("tts.engine_manager.PiperTTSEngine")
    @patch("tts.engine_manager.EdgeTTSEngine")
    def test_friendly_id_resolved(
        self,
        mock_edge_cls: MagicMock,
        mock_piper_cls: MagicMock,
        mock_sapi_cls: MagicMock,
    ) -> None:
        edge = _make_mock_engine("edge", available=True)
        edge.synthesize.return_value = _make_result()
        mock_edge_cls.return_value = edge
        mock_piper_cls.return_value = _make_mock_engine("piper", available=False)
        mock_sapi_cls.return_value = _make_mock_engine("sapi", available=False)

        mgr = EngineManager()
        mgr.initialize()
        mgr.synthesize("Hello", "guy-us")

        edge.synthesize.assert_called_once_with(
            "Hello", "en-US-GuyNeural", 1.0, 1.0
        )

    @patch("tts.engine_manager.SapiTTSEngine")
    @patch("tts.engine_manager.PiperTTSEngine")
    @patch("tts.engine_manager.EdgeTTSEngine")
    def test_unknown_id_passed_through(
        self,
        mock_edge_cls: MagicMock,
        mock_piper_cls: MagicMock,
        mock_sapi_cls: MagicMock,
    ) -> None:
        """An ID not in the catalog is assumed to be engine-specific."""
        edge = _make_mock_engine("edge", available=True)
        edge.synthesize.return_value = _make_result()
        mock_edge_cls.return_value = edge
        mock_piper_cls.return_value = _make_mock_engine("piper", available=False)
        mock_sapi_cls.return_value = _make_mock_engine("sapi", available=False)

        mgr = EngineManager()
        mgr.initialize()
        mgr.synthesize("Hello", "en-US-CustomNeural")

        edge.synthesize.assert_called_once_with(
            "Hello", "en-US-CustomNeural", 1.0, 1.0
        )


class TestGetAvailableVoices:
    @patch("tts.engine_manager.SapiTTSEngine")
    @patch("tts.engine_manager.PiperTTSEngine")
    @patch("tts.engine_manager.EdgeTTSEngine")
    def test_filters_by_available_engines(
        self,
        mock_edge_cls: MagicMock,
        mock_piper_cls: MagicMock,
        mock_sapi_cls: MagicMock,
    ) -> None:
        mock_edge_cls.return_value = _make_mock_engine("edge", available=True)
        mock_piper_cls.return_value = _make_mock_engine("piper", available=False)
        mock_sapi_cls.return_value = _make_mock_engine("sapi", available=False)

        mgr = EngineManager()
        mgr.initialize()
        voices = mgr.get_available_voices()

        # Only edge voices should be returned
        assert all(v.engine == "edge" for v in voices)
        assert len(voices) == 8
