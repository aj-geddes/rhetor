"""Settings management — JSON-backed persistent configuration."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

from constants import (
    DEFAULT_FONT_SIZE,
    DEFAULT_HIGHLIGHT_COLOR,
    DEFAULT_PARAGRAPH_PAUSE_MS,
    DEFAULT_SENTENCE_PAUSE_MS,
    DEFAULT_SPEED,
    DEFAULT_THEME,
    DEFAULT_VOLUME,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    MAX_RECENT_FILES,
    SETTINGS_FILE,
)

log = logging.getLogger(__name__)


@dataclass(slots=True)
class AppearanceSettings:
    theme: str = DEFAULT_THEME
    font_size: int = DEFAULT_FONT_SIZE
    highlight_color: str = DEFAULT_HIGHLIGHT_COLOR
    window_width: int = DEFAULT_WINDOW_WIDTH
    window_height: int = DEFAULT_WINDOW_HEIGHT
    window_x: int | None = None
    window_y: int | None = None


@dataclass(slots=True)
class VoiceSettings:
    preferred_engine: str = "auto"
    preferred_voice_id: str = "jenny-us"
    offline_voice_id: str = "amy-offline"
    force_offline: bool = False


@dataclass(slots=True)
class ReadingSettings:
    speed: float = DEFAULT_SPEED
    volume: float = DEFAULT_VOLUME
    pause_between_paragraphs_ms: int = DEFAULT_PARAGRAPH_PAUSE_MS
    pause_between_sentences_ms: int = DEFAULT_SENTENCE_PAUSE_MS
    announce_headings: bool = True
    skip_repeated_headers: bool = True


@dataclass(slots=True)
class Settings:
    version: str = "1.0"
    appearance: AppearanceSettings = field(default_factory=AppearanceSettings)
    voice: VoiceSettings = field(default_factory=VoiceSettings)
    reading: ReadingSettings = field(default_factory=ReadingSettings)
    recent_files: list[str] = field(default_factory=list)


class SettingsManager:
    """Load, save, and manage application settings."""

    def __init__(self, settings_path: Path | None = None) -> None:
        self._path = settings_path or SETTINGS_FILE
        self._settings = Settings()
        self.load()

    @property
    def settings(self) -> Settings:
        return self._settings

    def load(self) -> None:
        """Load settings from disk. Uses defaults if file missing or corrupt."""
        if not self._path.exists():
            return

        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            self._apply_dict(data)
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("Failed to load settings from %s: %s", self._path, exc)
            self._settings = Settings()

    def save(self) -> None:
        """Persist current settings to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(self._settings)
        self._path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def reset(self) -> None:
        """Reset all settings to defaults."""
        self._settings = Settings()

    def add_recent_file(self, file_path: str) -> None:
        """Add a file to the recent-files list (most recent first, deduped)."""
        recent = self._settings.recent_files
        # Remove if already present so it moves to front
        if file_path in recent:
            recent.remove(file_path)
        recent.insert(0, file_path)
        # Trim to max length
        self._settings.recent_files = recent[:MAX_RECENT_FILES]

    def _apply_dict(self, data: dict) -> None:  # type: ignore[type-arg]
        """Merge a JSON dict into settings, keeping defaults for missing keys."""
        s = self._settings
        s.version = data.get("version", s.version)
        s.recent_files = data.get("recent_files", s.recent_files)

        if "appearance" in data:
            a = data["appearance"]
            s.appearance = AppearanceSettings(
                theme=a.get("theme", DEFAULT_THEME),
                font_size=a.get("font_size", DEFAULT_FONT_SIZE),
                highlight_color=a.get("highlight_color", DEFAULT_HIGHLIGHT_COLOR),
                window_width=a.get("window_width", DEFAULT_WINDOW_WIDTH),
                window_height=a.get("window_height", DEFAULT_WINDOW_HEIGHT),
                window_x=a.get("window_x"),
                window_y=a.get("window_y"),
            )

        if "voice" in data:
            v = data["voice"]
            s.voice = VoiceSettings(
                preferred_engine=v.get("preferred_engine", "auto"),
                preferred_voice_id=v.get("preferred_voice_id", "jenny-us"),
                offline_voice_id=v.get("offline_voice_id", "amy-offline"),
                force_offline=v.get("force_offline", False),
            )

        if "reading" in data:
            r = data["reading"]
            s.reading = ReadingSettings(
                speed=r.get("speed", DEFAULT_SPEED),
                volume=r.get("volume", DEFAULT_VOLUME),
                pause_between_paragraphs_ms=r.get(
                    "pause_between_paragraphs_ms", DEFAULT_PARAGRAPH_PAUSE_MS
                ),
                pause_between_sentences_ms=r.get(
                    "pause_between_sentences_ms", DEFAULT_SENTENCE_PAUSE_MS
                ),
                announce_headings=r.get("announce_headings", True),
                skip_repeated_headers=r.get("skip_repeated_headers", True),
            )
