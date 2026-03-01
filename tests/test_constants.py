"""Tests for application constants."""

from pathlib import Path

from constants import (
    APP_NAME,
    APP_VERSION,
    ASSETS_DIR,
    CONFIG_DIR,
    DEFAULT_FONT_SIZE,
    DEFAULT_SPEED,
    DEFAULT_WORDS_PER_MINUTE,
    FORMAT_DESCRIPTIONS,
    MAX_RECENT_FILES,
    SETTINGS_FILE,
    SUPPORTED_FORMATS,
    WINDOW_TITLE,
)


class TestAppIdentity:
    def test_app_name(self) -> None:
        assert APP_NAME == "Rhetor"

    def test_version_format(self) -> None:
        # Should be a semver-like string
        parts = APP_VERSION.replace("-dev", "").split(".")
        assert len(parts) == 3

    def test_window_title_contains_name(self) -> None:
        assert APP_NAME in WINDOW_TITLE


class TestSupportedFormats:
    def test_four_formats(self) -> None:
        assert len(SUPPORTED_FORMATS) == 4

    def test_expected_formats(self) -> None:
        assert ".txt" in SUPPORTED_FORMATS
        assert ".md" in SUPPORTED_FORMATS
        assert ".docx" in SUPPORTED_FORMATS
        assert ".pdf" in SUPPORTED_FORMATS

    def test_is_frozenset(self) -> None:
        assert isinstance(SUPPORTED_FORMATS, frozenset)

    def test_format_descriptions_match(self) -> None:
        assert set(FORMAT_DESCRIPTIONS.keys()) == SUPPORTED_FORMATS


class TestPaths:
    def test_config_dir_is_path(self) -> None:
        assert isinstance(CONFIG_DIR, Path)

    def test_settings_file_under_config(self) -> None:
        assert SETTINGS_FILE.parent == CONFIG_DIR

    def test_assets_dir_is_path(self) -> None:
        assert isinstance(ASSETS_DIR, Path)


class TestDefaults:
    def test_wpm_reasonable(self) -> None:
        assert 100 <= DEFAULT_WORDS_PER_MINUTE <= 300

    def test_font_size_reasonable(self) -> None:
        assert 8 <= DEFAULT_FONT_SIZE <= 32

    def test_speed_default(self) -> None:
        assert DEFAULT_SPEED == 1.0

    def test_max_recent(self) -> None:
        assert MAX_RECENT_FILES >= 5
