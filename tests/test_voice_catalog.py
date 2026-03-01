"""Tests for VoiceCatalog — lookup, filtering, and dynamic registration."""

from __future__ import annotations

from tts.models import VoiceInfo
from tts.voice_catalog import VoiceCatalog


class TestVoiceCatalog:
    def test_get_voice_existing(self) -> None:
        catalog = VoiceCatalog()
        voice = catalog.get_voice("jenny-us")
        assert voice is not None
        assert voice.voice_id == "jenny-us"
        assert voice.engine == "edge"

    def test_get_voice_not_found(self) -> None:
        catalog = VoiceCatalog()
        assert catalog.get_voice("nonexistent-voice") is None

    def test_get_all_voices_count(self) -> None:
        catalog = VoiceCatalog()
        voices = catalog.get_all_voices()
        assert len(voices) == 11  # 8 edge + 3 piper

    def test_get_voices_for_edge(self) -> None:
        catalog = VoiceCatalog()
        edge_voices = catalog.get_voices_for_engine("edge")
        assert len(edge_voices) == 8
        assert all(v.engine == "edge" for v in edge_voices)

    def test_get_voices_for_piper(self) -> None:
        catalog = VoiceCatalog()
        piper_voices = catalog.get_voices_for_engine("piper")
        assert len(piper_voices) == 3
        assert all(v.engine == "piper" for v in piper_voices)

    def test_get_voices_for_nonexistent_engine(self) -> None:
        catalog = VoiceCatalog()
        assert catalog.get_voices_for_engine("nonexistent") == []

    def test_get_online_voices(self) -> None:
        catalog = VoiceCatalog()
        online = catalog.get_online_voices()
        assert len(online) == 8  # all edge voices
        assert all(v.requires_internet for v in online)

    def test_get_offline_voices(self) -> None:
        catalog = VoiceCatalog()
        offline = catalog.get_offline_voices()
        assert len(offline) == 3  # all piper voices
        assert all(not v.requires_internet for v in offline)

    def test_register_voice(self) -> None:
        catalog = VoiceCatalog()
        new_voice = VoiceInfo(
            voice_id="sapi-david",
            name="David",
            engine="sapi",
            engine_voice_id="HKEY_LOCAL_MACHINE\\David",
        )
        catalog.register_voice(new_voice)
        assert catalog.get_voice("sapi-david") is not None
        assert len(catalog.get_all_voices()) == 12

    def test_register_duplicate_skipped(self) -> None:
        catalog = VoiceCatalog()
        original_count = len(catalog.get_all_voices())
        duplicate = VoiceInfo(
            voice_id="jenny-us",
            name="Jenny Duplicate",
            engine="edge",
            engine_voice_id="en-US-JennyNeural",
        )
        catalog.register_voice(duplicate)
        assert len(catalog.get_all_voices()) == original_count
        # Original should be preserved
        voice = catalog.get_voice("jenny-us")
        assert voice is not None
        assert voice.name == "Jenny (US)"

    def test_edge_voice_ids(self) -> None:
        """Verify all expected edge voice IDs are present."""
        catalog = VoiceCatalog()
        expected = {
            "jenny-us", "guy-us", "aria-us", "andrew-us",
            "sonia-gb", "ryan-gb", "natasha-au", "william-au",
        }
        actual = {v.voice_id for v in catalog.get_voices_for_engine("edge")}
        assert actual == expected

    def test_piper_voice_ids(self) -> None:
        """Verify all expected piper voice IDs are present."""
        catalog = VoiceCatalog()
        expected = {"lessac-offline", "amy-offline", "alba-offline"}
        actual = {v.voice_id for v in catalog.get_voices_for_engine("piper")}
        assert actual == expected

    def test_edge_voices_require_internet(self) -> None:
        catalog = VoiceCatalog()
        for voice in catalog.get_voices_for_engine("edge"):
            assert voice.requires_internet is True

    def test_piper_voices_offline(self) -> None:
        catalog = VoiceCatalog()
        for voice in catalog.get_voices_for_engine("piper"):
            assert voice.requires_internet is False
