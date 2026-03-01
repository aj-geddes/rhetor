"""Tests for settings management."""

import json
from pathlib import Path

from config import AppearanceSettings, ReadingSettings, Settings, SettingsManager, VoiceSettings


class TestSettingsDefaults:
    def test_appearance_defaults(self) -> None:
        a = AppearanceSettings()
        assert a.theme == "system"
        assert a.font_size == 14
        assert a.window_x is None

    def test_voice_defaults(self) -> None:
        v = VoiceSettings()
        assert v.preferred_engine == "auto"
        assert v.force_offline is False

    def test_reading_defaults(self) -> None:
        r = ReadingSettings()
        assert r.speed == 1.0
        assert r.volume == 0.8
        assert r.announce_headings is True

    def test_settings_defaults(self) -> None:
        s = Settings()
        assert s.version == "1.0"
        assert s.recent_files == []


class TestSettingsManager:
    def test_load_missing_file(self, tmp_path: Path) -> None:
        mgr = SettingsManager(settings_path=tmp_path / "nonexistent.json")
        assert mgr.settings.version == "1.0"

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.json"
        mgr = SettingsManager(settings_path=path)
        mgr.settings.appearance.font_size = 18
        mgr.settings.voice.force_offline = True
        mgr.settings.reading.speed = 1.5
        mgr.save()

        mgr2 = SettingsManager(settings_path=path)
        assert mgr2.settings.appearance.font_size == 18
        assert mgr2.settings.voice.force_offline is True
        assert mgr2.settings.reading.speed == 1.5

    def test_reset(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.json"
        mgr = SettingsManager(settings_path=path)
        mgr.settings.appearance.font_size = 99
        mgr.reset()
        assert mgr.settings.appearance.font_size == 14

    def test_add_recent_file(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.json"
        mgr = SettingsManager(settings_path=path)
        mgr.add_recent_file("/path/to/file1.pdf")
        mgr.add_recent_file("/path/to/file2.txt")
        assert mgr.settings.recent_files[0] == "/path/to/file2.txt"
        assert mgr.settings.recent_files[1] == "/path/to/file1.pdf"

    def test_add_recent_deduplicates(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.json"
        mgr = SettingsManager(settings_path=path)
        mgr.add_recent_file("/path/a.pdf")
        mgr.add_recent_file("/path/b.pdf")
        mgr.add_recent_file("/path/a.pdf")  # should move to front
        assert mgr.settings.recent_files == ["/path/a.pdf", "/path/b.pdf"]

    def test_add_recent_max_limit(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.json"
        mgr = SettingsManager(settings_path=path)
        for i in range(15):
            mgr.add_recent_file(f"/path/file{i}.pdf")
        assert len(mgr.settings.recent_files) == 10

    def test_corrupt_json_uses_defaults(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.json"
        path.write_text("{{{invalid json", encoding="utf-8")
        mgr = SettingsManager(settings_path=path)
        assert mgr.settings.version == "1.0"
        assert mgr.settings.appearance.font_size == 14

    def test_partial_json_fills_defaults(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.json"
        path.write_text(
            json.dumps({"version": "1.0", "appearance": {"font_size": 20}}),
            encoding="utf-8",
        )
        mgr = SettingsManager(settings_path=path)
        assert mgr.settings.appearance.font_size == 20
        assert mgr.settings.appearance.theme == "system"  # default
        assert mgr.settings.voice.preferred_engine == "auto"  # default

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        path = tmp_path / "sub" / "dir" / "settings.json"
        mgr = SettingsManager(settings_path=path)
        mgr.save()
        assert path.exists()
