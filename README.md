# Rhetor

**The Master Orator for Your Documents**

Rhetor is a Windows desktop application that reads documents aloud using high-quality text-to-speech. Open a PDF, Word document, Markdown file, or plain text file and listen hands-free with natural-sounding voices.

## Features

- **Four document formats** -- Plain text (.txt), Markdown (.md), Word (.docx), and PDF (.pdf)
- **Three TTS engine tiers** with automatic failover:
  - **Edge TTS** -- Microsoft neural voices (online, highest quality)
  - **Piper TTS** -- Neural ONNX models (offline, high quality)
  - **SAPI** -- Built-in Windows voices (offline, always available)
- **11+ voices** -- 8 Edge neural voices (US, GB, AU accents), 3 Piper offline voices, plus any installed Windows SAPI voices
- **Full playback controls** -- Play, pause, stop, skip by sentence or paragraph
- **Live adjustments** -- Change voice, speed (0.5x--2.0x), and volume during playback
- **Keyboard-driven** -- 15 shortcuts for every action
- **Drag and drop** -- Drop files directly onto the window
- **Dark/light themes** -- System-aware or manual toggle
- **Persistent settings** -- Window position, voice preferences, speed, and volume saved across sessions
- **Standalone .exe** -- No Python installation required for end users

## Quick Start

### For Users (Standalone)

Download and run `Rhetor.exe`. No installation needed.

1. Open a document with **File > Open** or **Ctrl+O**
2. Press **Space** to start reading
3. Use the toolbar to change voice, speed, or volume

### For Developers

Requires Python 3.10--3.13.

```bash
# Clone and install
git clone <repo-url>
cd rhetor
pip install -e ".[dev]"

# Run
python main.py

# Run tests
python -m pytest -v

# Lint and type check
ruff check .
mypy .
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Space | Play / Pause |
| Escape | Stop |
| Left / Right | Previous / Next sentence |
| Ctrl+Left / Right | Previous / Next paragraph |
| Ctrl+Up / Down | Speed +/- 0.25x |
| Up / Down | Volume +/- 5% |
| Ctrl+O | Open file |
| Ctrl+Q | Quit |
| Ctrl+D | Toggle dark/light theme |
| Ctrl+, | Settings |
| F1 | User Guide |

## Architecture

```
rhetor/
  main.py              Entry point
  app.py               Application controller (owns window, engines, playback)
  constants.py         App-wide constants, paths, defaults
  config.py            Settings persistence (JSON)
  core/                Business logic (zero UI imports)
    models.py          ReadingChunk, ParsedDocument, TextElement
    parsers/           Format-specific parsers (text, markdown, docx, pdf)
    document_loader.py File dispatch by extension
    text_processor.py  Sentence segmentation and chunking
    reading_session.py Navigation state (position, paragraph skip)
  tts/                 Text-to-speech abstraction
    base_engine.py     TTSEngine Protocol + error hierarchy
    edge_engine.py     Microsoft Edge TTS (Tier 1, online)
    piper_engine.py    Piper neural TTS (Tier 2, offline)
    sapi_engine.py     Windows SAPI5 (Tier 3, offline)
    engine_manager.py  Engine selection, failover, voice resolution
    voice_catalog.py   Curated voice registry
  audio/               Audio playback pipeline
    buffer.py          Bounded thread-safe queue
    audio_thread.py    TTSWorker + AudioPlayer daemon threads
    player.py          PlaybackController (public API, state machine)
  ui/                  CustomTkinter desktop UI
    main_window.py     Layout, menus, keyboard shortcuts, drag-and-drop
    document_view.py   Text display with chunk highlighting
    toolbar.py         Playback buttons, voice dropdown, sliders
    status_bar.py      State, progress, time remaining, errors
    settings_dialog.py Tabbed settings (Appearance, Voice, Reading)
    user_guide.py      Searchable in-app user guide
  assets/
    user_guide.md      User guide content
  build/
    build.sh           WSL2 build script (syncs to Windows, runs PyInstaller)
    rhetor.spec        PyInstaller spec (one-directory, windowed)
  tests/               372 tests (pytest)
```

### Design Principles

- **`core/` has zero UI imports** -- business logic is fully decoupled from the interface
- **Protocol-based abstractions** -- parsers and TTS engines use structural subtyping, not ABC
- **Frozen dataclasses with `__slots__`** -- immutable data models for thread safety
- **Daemon threads with event signaling** -- TTSWorker synthesizes ahead into a bounded buffer; AudioPlayer consumes via pygame; `threading.Event` for stop/pause/skip
- **Thread-safe playback** -- all PlaybackController methods are safe to call from any thread; UI events marshaled via `root.after()`
- **Three-tier failover** -- if Edge TTS is unavailable (no internet), falls back to Piper, then SAPI

## Building the Standalone .exe

Builds run from WSL2 using Windows Python to produce a native Windows executable.

**Prerequisites:**
- WSL2 with `rsync` installed
- Python 3.13 installed on Windows at `C:\Python313\python.exe`

```bash
# From the project root in WSL2:
bash build/build.sh
```

Output: `C:\Users\Munso\rhetor-app\dist\Rhetor\Rhetor.exe` (~151 MB bundle)

The build script:
1. Syncs source to the Windows filesystem
2. Creates a Windows venv and installs dependencies
3. Runs PyInstaller (one-directory mode, no console window)
4. Bundles assets (user guide, voice models directory)

## Voices

### Edge TTS (Online)

| Voice | Accent | Gender |
|-------|--------|--------|
| Jenny | US | Female |
| Guy | US | Male |
| Aria | US | Female |
| Andrew | US | Male |
| Sonia | GB | Female |
| Ryan | GB | Male |
| Natasha | AU | Female |
| William | AU | Male |

### Piper TTS (Offline)

| Voice | Quality | Description |
|-------|---------|-------------|
| Amy | Medium | British female |
| Lessac | Medium | American male |
| Kristin | Medium | American female |

### SAPI (Windows Built-in)

Any voices installed on the Windows system are automatically discovered and available.

## Configuration

Settings are stored as JSON in the platform-appropriate config directory:
- **Windows:** `%APPDATA%\Rhetor\settings.json`
- **Linux:** `~/.config/Rhetor/settings.json`

## Testing

```bash
# Full suite (372 tests)
python -m pytest -v

# Specific module
python -m pytest tests/test_text_processor.py -v

# With coverage
python -m pytest --cov=. --cov-report=term-missing
```

All test fixtures are generated programmatically -- no binary test files are committed.

## Dependencies

| Package | Purpose |
|---------|---------|
| pymupdf | PDF text extraction |
| python-docx | Word document parsing |
| charset-normalizer | Text file encoding detection |
| edge-tts | Microsoft neural TTS (online) |
| piper-tts | Neural TTS with ONNX models (offline) |
| pyttsx3 | Windows SAPI5 TTS bridge |
| pygame | Audio playback via SDL mixer |
| customtkinter | Modern themed tkinter widgets |

## License

Proprietary. Created by AJ Geddes / High Velocity Solutions LLC.
