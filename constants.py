"""Application-wide constants, paths, and defaults."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# ── App Identity ──────────────────────────────────────────────────────────────

APP_NAME = "Rhetor"
APP_VERSION = "1.0.0-dev"
APP_TAGLINE = "The Master Orator for Your Documents"
APP_AUTHOR = "High Velocity Solutions LLC"
WINDOW_TITLE = f"{APP_NAME} \u2014 Document Reader"

# ── Supported Formats ─────────────────────────────────────────────────────────

SUPPORTED_FORMATS: frozenset[str] = frozenset({".txt", ".md", ".docx", ".pdf"})

FORMAT_DESCRIPTIONS: dict[str, str] = {
    ".txt": "Plain Text",
    ".md": "Markdown",
    ".docx": "Word Document",
    ".pdf": "PDF Document",
}

# ── Paths ─────────────────────────────────────────────────────────────────────


def _get_config_dir() -> Path:
    """Return the platform-appropriate configuration directory."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / APP_NAME


CONFIG_DIR: Path = _get_config_dir()
SETTINGS_FILE: Path = CONFIG_DIR / "settings.json"
LOG_DIR: Path = CONFIG_DIR / "logs"
ASSETS_DIR: Path = Path(__file__).resolve().parent / "assets"

# ── Text Processing Defaults ─────────────────────────────────────────────────

DEFAULT_WORDS_PER_MINUTE: int = 175
MIN_CHUNK_LENGTH: int = 1
MAX_CHUNK_LENGTH: int = 5000

# ── Settings Defaults ─────────────────────────────────────────────────────────

DEFAULT_THEME: str = "system"
DEFAULT_FONT_SIZE: int = 14
DEFAULT_HIGHLIGHT_COLOR: str = "#d4a843"
DEFAULT_WINDOW_WIDTH: int = 900
DEFAULT_WINDOW_HEIGHT: int = 700

DEFAULT_SPEED: float = 1.0
DEFAULT_VOLUME: float = 0.8
DEFAULT_PARAGRAPH_PAUSE_MS: int = 500
DEFAULT_SENTENCE_PAUSE_MS: int = 100

MAX_RECENT_FILES: int = 10

# ── TTS Defaults ─────────────────────────────────────────────────────────────

PIPER_MODELS_DIR: Path = ASSETS_DIR / "voices"
CONNECTIVITY_TIMEOUT_S: float = 3.0
MIN_SPEED: float = 0.5
MAX_SPEED: float = 2.0
SAPI_BASE_WPM: int = 200
