# Rhetor — Application Planning Document

> *"The Master Orator for Your Documents"*

**Project:** Rhetor — Windows Desktop Document Reader
**Version:** MVP (1.0)
**Author:** AJ Geddes / High Velocity Solutions LLC
**Date:** March 2026
**Status:** Planning Phase

---

## 1. Product Vision

Rhetor is a Windows desktop application that reads documents aloud using natural-sounding voices. Named after the Greek word for "master orator," Rhetor transforms silent documents into spoken word — giving every PDF, Word doc, markdown file, and text file a golden voice.

### 1.1 Core Value Proposition

Most existing document readers fall into two camps: free tools with robotic voices that are painful to listen to, or cloud-dependent services that require subscriptions and internet connectivity. Rhetor occupies the sweet spot — high-quality neural voices with a clean, focused interface, delivered as a standalone Windows application.

### 1.2 Target Users

- **Professionals** who consume large volumes of reports, proposals, and documentation and want to "read" while multitasking
- **Students and researchers** processing academic papers and study materials
- **Accessibility-minded users** who benefit from audio presentation of written content
- **Content creators** who want to hear their own writing read back to them for editing and flow-checking
- **Anyone with eye fatigue** who wants to rest their eyes while still consuming written content

### 1.3 MVP Scope

| Feature | Included | Notes |
|---|---|---|
| .md file support | ✅ | Strip formatting, read clean text |
| .txt file support | ✅ | Direct text reading |
| .docx file support | ✅ | Extract text preserving reading order |
| .pdf file support | ✅ | Extract text with layout awareness |
| Natural neural voices | ✅ | Multiple voice options, male and female |
| Playback controls | ✅ | Play, pause, stop, skip forward/back |
| Speed control | ✅ | 0.5x to 2.0x reading speed |
| Built-in user guide | ✅ | Accessible from Help menu and welcome screen |
| Clean modern UI | ✅ | Dark/light mode, minimal chrome |
| Offline capability | ✅ | At least one high-quality offline voice engine |
| Online voices | ✅ | Premium neural voices when internet available |
| Bookmarking/position memory | ❌ | Deferred to v1.1 |
| Epub/HTML support | ❌ | Deferred to v1.1 |
| Voice cloning | ❌ | Deferred to v2.0 |
| Export to audio file | ❌ | Deferred to v1.1 |

---

## 2. Branding & Identity

### 2.1 Name

**Rhetor** (ˈrɛtər) — from Ancient Greek *rhḗtōr* (ῥήτωρ), meaning "public speaker, orator, master of rhetoric." In classical Athens, a rhetor was someone trained in the art of persuasive and eloquent speech. The name positions the application as the authoritative voice for your documents.

### 2.2 Tagline Options

- *"The Master Orator for Your Documents"* (primary)
- *"Give Your Documents a Voice"*
- *"Your Documents, Eloquently Spoken"*
- *"Read Aloud, Done Right"*

### 2.3 Visual Identity Direction

- **Icon concept:** A stylized Greek column or scroll combined with a sound wave or speaker glyph. The icon should work at 16x16 (taskbar) through 256x256 (installer). Consider a simple laurel wreath enclosing a speaker/sound wave symbol.
- **Color palette:** Deep navy/indigo primary (#1a1a2e or similar), warm gold accent (#d4a843), clean whites and soft grays. The palette should evoke authority and warmth — a scholarly but approachable feel.
- **Typography direction:** Clean sans-serif for the UI (the app ships with system fonts). The logo/splash could use a serif or semi-serif typeface to echo classical roots.

### 2.4 Application Metadata

- **Executable name:** `Rhetor.exe`
- **Window title:** `Rhetor — Document Reader`
- **Install directory default:** `C:\Program Files\Rhetor\`
- **User data directory:** `%APPDATA%\Rhetor\`
- **Config file:** `%APPDATA%\Rhetor\settings.json`

---

## 3. Technical Architecture

### 3.1 Technology Stack Decision Matrix

#### 3.1.1 GUI Framework: **CustomTkinter** (Recommended for MVP)

| Framework | Pros | Cons | Verdict |
|---|---|---|---|
| **CustomTkinter** | Modern look out of the box, dark/light mode built-in, extremely fast to develop, lightweight, Tkinter is in stdlib | Less powerful for complex layouts, limited widget ecosystem vs Qt | **✅ Best for MVP** |
| **PySide6 (Qt)** | Industry-grade, massive widget set, professional polish, Qt Designer for layouts | Steep learning curve, large deployment size (~80-150MB), overkill for MVP | Good for v2.0 migration |
| **Flet** | Flutter-based, beautiful by default, hot reload | Newer/less mature, web-first mentality, less desktop-native feel | Not recommended yet |

**Rationale:** CustomTkinter delivers a clean, modern interface with dark/light theme support and HighDPI scaling on Windows with minimal code. For an MVP focused on reading documents aloud, we don't need Qt's complexity. The entire UI is essentially: a file browser, a text display area, playback controls, and a settings panel. CustomTkinter handles this elegantly. If Rhetor evolves into a more complex product, migrating to PySide6 is a clean future path.

#### 3.1.2 TTS Engine Strategy: **Tiered Approach**

Rhetor uses a tiered voice engine architecture — offering both offline and online voices so the app always works, but sounds *best* with an internet connection.

**Tier 1 — Online Premium (Default when connected): `edge-tts`**

- Accesses Microsoft's neural TTS voices (same engine as Edge browser's "Read Aloud")
- 400+ voices across 100+ languages
- Extremely natural sounding — among the best free neural voices available
- No API key required, no account needed
- Async Python API, supports rate/pitch/volume adjustment
- Generates audio as MP3 stream
- **Caveat:** Requires internet. Microsoft could theoretically rate-limit or deprecate access. This is why Tier 2 exists.
- **Key English voices to curate for MVP:**
  - `en-US-GuyNeural` — Natural male, warm and clear
  - `en-US-JennyNeural` — Natural female, professional tone
  - `en-US-AriaNeural` — Expressive female, excellent for narratives
  - `en-US-AndrewNeural` — Calm male, good for long-form reading
  - `en-GB-SoniaNeural` — British female, polished
  - `en-GB-RyanNeural` — British male, authoritative
  - `en-AU-NatashaNeural` — Australian female
  - `en-AU-WilliamNeural` — Australian male

**Tier 2 — Offline Fallback: `piper-tts`**

- Fast, local neural TTS using ONNX models (VITS architecture)
- Runs entirely on CPU — no GPU required, no internet needed
- pip-installable (`piper-tts`), Windows wheels available
- Multiple quality levels per voice (low/medium/high)
- Ship 2-3 bundled voice models (~15-50MB each for medium quality)
- **Recommended bundled voices:**
  - `en_US-lessac-medium` — High quality US English male
  - `en_US-amy-medium` — US English female
  - `en_GB-alba-medium` — British English female
- Speed adjustable via `length_scale` parameter in model config
- Noticeably less natural than edge-tts, but very good for offline/fallback

**Tier 3 — System Fallback: `pyttsx3`**

- Uses Windows SAPI5 built-in voices
- Zero dependencies, always available
- Voice quality is the worst of the three tiers but functional
- Serves as the ultimate fallback if both edge-tts and piper have issues

**Engine Selection Logic:**

```
User opens app:
  → Check internet connectivity
  → If online AND user hasn't forced offline mode:
      → Use edge-tts (Tier 1)
  → Else if piper models are installed:
      → Use piper-tts (Tier 2)
  → Else:
      → Use pyttsx3 / SAPI5 (Tier 3)

User can override in Settings:
  → "Always use offline voices"
  → "Preferred engine" dropdown
  → "Preferred voice" per engine
```

#### 3.1.3 Document Parsing Libraries

| Format | Library | Rationale |
|---|---|---|
| **.pdf** | `pymupdf` (PyMuPDF) | Fastest Python PDF parser, excellent text extraction with reading order preservation, handles complex layouts, tables, multi-column. Active development, well-documented. |
| **.docx** | `python-docx` | Standard library for Word document parsing. Extracts paragraphs, headings, lists in reading order. Handles styles and formatting metadata. |
| **.md** | `markdown` + custom stripping | Parse markdown to extract plain text content. Strip formatting syntax (headers become text, links become link text, code blocks preserved as-is). Use regex-based stripping for speed. |
| **.txt** | Built-in Python `open()` | Direct file read with encoding detection via `chardet` or `charset-normalizer`. Handle UTF-8, Latin-1, Windows-1252 gracefully. |

**Text Preprocessing Pipeline (all formats):**

```
Raw Document → Format-Specific Parser → Plain Text Extraction
  → Sentence Segmentation (split on ., !, ?, paragraph breaks)
  → Whitespace Normalization
  → Optional: Skip headers/footers/page numbers (PDF)
  → Chunked Text Queue (for streaming TTS)
```

#### 3.1.4 Audio Playback

| Component | Library | Purpose |
|---|---|---|
| Audio output | `pygame.mixer` or `sounddevice` | Play generated audio chunks in real-time |
| Audio buffering | `io.BytesIO` + threading | Buffer TTS output ahead of playback position |
| Stream management | `asyncio` + `threading` | edge-tts is async; bridge to sync playback thread |

**Recommended: `pygame.mixer`** — battle-tested, handles MP3 natively, lightweight, excellent Windows support. The mixer module alone can be imported without pulling in the full pygame game framework.

Alternative: `sounddevice` + `soundfile` for lower-level control (better for piper-tts WAV streaming).

**Architecture Decision:** Use an audio abstraction layer that normalizes output from all three TTS engines into a common playback interface. Each engine produces audio differently:
- `edge-tts` → MP3 bytes (async stream)
- `piper-tts` → WAV/PCM bytes (sync stream)  
- `pyttsx3` → Direct SAPI playback (has its own audio output)

The abstraction layer converts everything to a common format for the playback controller.

### 3.2 Application Architecture

```
rhetor/
├── main.py                    # Entry point, app initialization
├── app.py                     # Main application window (CustomTkinter CTk)
├── config.py                  # Settings management (JSON read/write)
├── constants.py               # App-wide constants, paths, defaults
│
├── ui/                        # All UI components
│   ├── __init__.py
│   ├── main_window.py         # Primary window layout and orchestration
│   ├── toolbar.py             # Top toolbar (open file, settings, help)
│   ├── document_view.py       # Scrollable text display with highlight
│   ├── playback_controls.py   # Play/pause/stop, progress, speed slider
│   ├── voice_selector.py      # Voice picker dropdown with preview
│   ├── settings_dialog.py     # Settings/preferences modal
│   ├── user_guide_dialog.py   # Built-in help/user guide window
│   ├── welcome_screen.py      # First-run / no-document-loaded view
│   └── theme.py               # Color constants, font definitions
│
├── core/                      # Business logic (zero UI imports)
│   ├── __init__.py
│   ├── document_loader.py     # Unified document loading interface
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── pdf_parser.py      # PyMuPDF-based PDF text extraction
│   │   ├── docx_parser.py     # python-docx text extraction
│   │   ├── markdown_parser.py # Markdown → plain text
│   │   └── text_parser.py     # Plain text with encoding detection
│   ├── text_processor.py      # Sentence segmentation, chunking, cleanup
│   └── reading_session.py     # Manages current document state and position
│
├── tts/                       # Text-to-speech engine abstraction
│   ├── __init__.py
│   ├── engine_manager.py      # Engine selection, initialization, failover
│   ├── base_engine.py         # Abstract base class for TTS engines
│   ├── edge_engine.py         # edge-tts wrapper (online neural voices)
│   ├── piper_engine.py        # piper-tts wrapper (offline neural voices)
│   ├── sapi_engine.py         # pyttsx3/SAPI5 wrapper (system fallback)
│   └── voice_catalog.py       # Curated voice list with metadata
│
├── audio/                     # Audio playback management
│   ├── __init__.py
│   ├── player.py              # Unified audio playback controller
│   ├── buffer.py              # Pre-buffering and streaming logic
│   └── audio_thread.py        # Background thread for non-blocking audio
│
├── assets/                    # Static resources
│   ├── icons/                 # App icon in multiple sizes (.ico, .png)
│   ├── fonts/                 # Any bundled fonts (if needed)
│   ├── voices/                # Bundled piper voice models (.onnx + .json)
│   └── user_guide.md          # The built-in user guide content
│
├── tests/                     # Test suite
│   ├── test_parsers.py
│   ├── test_text_processor.py
│   ├── test_tts_engines.py
│   ├── test_audio_player.py
│   └── fixtures/              # Sample .pdf, .docx, .md, .txt files
│
├── build/                     # Build and packaging configuration
│   ├── rhetor.spec            # PyInstaller spec file
│   ├── rhetor.ico             # Application icon
│   ├── installer/             # InstallForge or Inno Setup config
│   └── build.ps1              # Windows build script
│
├── pyproject.toml             # Project metadata, dependencies
├── requirements.txt           # Pinned dependencies for build
├── README.md                  # Developer documentation
├── LICENSE                    # License file
└── .pre-commit-config.yaml    # Code quality hooks
```

### 3.3 Threading Model

This is critical for a responsive UI. TTS generation and audio playback MUST NOT block the UI thread.

```
┌─────────────────────────────────────────────────┐
│                  Main Thread                     │
│            (CustomTkinter UI Loop)               │
│                                                  │
│  User clicks Play → Sends command to Controller  │
│  Controller updates UI (progress, highlighting)  │
│  via .after() callbacks from worker threads      │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐   ┌───────▼────────┐
│  TTS Worker    │   │  Audio Player  │
│  Thread        │   │  Thread        │
│                │   │                │
│  Takes text    │   │  Takes audio   │
│  chunks from   │──▶│  chunks from   │
│  queue, runs   │   │  buffer queue, │
│  TTS engine,   │   │  plays them    │
│  puts audio    │   │  sequentially  │
│  in buffer     │   │                │
└────────────────┘   └────────────────┘
```

**Key threading rules:**
- UI thread only touches CustomTkinter widgets
- TTS worker thread handles all synthesis (edge-tts async loop runs here)
- Audio player thread handles all playback
- Communication between threads uses `queue.Queue` (thread-safe)
- UI updates from worker threads use `root.after()` to schedule callbacks on the main thread
- Graceful shutdown: cancel flags checked in worker loops, threads joined on exit

### 3.4 Dependency List (MVP)

```toml
[project]
requires-python = ">=3.10,<3.13"

dependencies = [
    "customtkinter>=5.2.0",       # Modern UI framework
    "edge-tts>=7.2.0",            # Microsoft neural voices (online)
    "piper-tts>=1.4.0",           # Neural voices (offline)
    "pyttsx3>=2.90",              # SAPI5 system fallback
    "pymupdf>=1.24.0",            # PDF parsing
    "python-docx>=1.1.0",         # DOCX parsing
    "charset-normalizer>=3.3.0",  # Text encoding detection
    "Pillow>=10.0.0",             # Image handling for UI assets
    "pygame>=2.5.0",              # Audio playback (mixer module)
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.4.0",
    "mypy>=1.10",
    "pyinstaller>=6.5",
    "pre-commit>=3.7",
]
```

---

## 4. User Experience Design

### 4.1 Design Principles

1. **Invisible complexity** — The user should never think about TTS engines, audio formats, or text extraction. They open a file and press play.
2. **Immediate value** — The app should be usable within 5 seconds of first launch. No setup wizards, no account creation, no configuration required.
3. **Forgiving interaction** — Every action is undoable or restartable. Pause doesn't lose position. Closing the app remembers where you left off (v1.1 — for MVP, simply restart from beginning).
4. **Visual feedback** — The currently-spoken sentence is always highlighted in the document view. Progress is always visible.
5. **Quiet confidence** — The UI should feel calm and professional. No animations for animation's sake. No gratuitous color. Let the content breathe.

### 4.2 Screen Layout — Main Window

```
┌─────────────────────────────────────────────────────────────┐
│  ┌─────┐  Rhetor                              ─  □  ✕      │
│  │ ico │  Document Reader                                   │
├─────────────────────────────────────────────────────────────┤
│  [📂 Open]  [Voice: Jenny (US) ▾]  [⚙ Settings]  [? Help]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                                                     │   │
│   │  Document text displayed here in a scrollable       │   │
│   │  readable view. The current sentence being read     │   │
│   │  is highlighted with a subtle background color.     │   │
│   │                                                     │   │
│   │  ▐ This sentence is currently being spoken. ▐       │   │
│   │                                                     │   │
│   │  The text continues below with clear paragraph      │   │
│   │  spacing and a comfortable reading font size.       │   │
│   │                                                     │   │
│   │  The view auto-scrolls to keep the highlighted      │   │
│   │  sentence centered (or near-top) in the viewport.   │   │
│   │                                                     │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ◁◁  [  ▶ PLAY  ]  ▷▷        ━━━━━━●━━━━━━━  3:42/12:15  │
│                                                             │
│   Speed: [  1.0x  ▾]     Vol: ━━━━━━●━━━  🔊               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Screen Layout — Welcome Screen (No Document Loaded)

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                                                             │
│                       ⚱  RHETOR                             │
│                  The Master Orator                          │
│                for Your Documents                           │
│                                                             │
│                                                             │
│              ┌───────────────────────────┐                  │
│              │                           │                  │
│              │   Drop a file here        │                  │
│              │   or click to browse      │                  │
│              │                           │                  │
│              │   Supports: .pdf .docx    │                  │
│              │             .md  .txt     │                  │
│              │                           │                  │
│              └───────────────────────────┘                  │
│                                                             │
│              ┌──────────────────────┐                       │
│              │  📖 Read User Guide  │                       │
│              └──────────────────────┘                       │
│                                                             │
│                  Voice: ● Online (Jenny)                    │
│                  Engine: edge-tts (connected)               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 User Interaction Flows

**Flow 1: First Launch**
1. App opens to Welcome Screen
2. Status bar shows detected TTS engine and connectivity
3. User can immediately drag-and-drop a file or click "Open"
4. Optional: subtle tooltip pointing to "Help" for the user guide

**Flow 2: Opening and Reading a Document**
1. User opens file (drag-drop, Open button, or File menu)
2. Loading indicator shows briefly while document is parsed
3. Document text appears in the reading view
4. User clicks Play
5. TTS begins from the top; currently-spoken sentence highlights
6. View auto-scrolls to follow the reading position
7. User can pause, adjust speed, or change voice at any time
8. Changing voice mid-read: current position is preserved, new voice takes over from the current sentence

**Flow 3: Changing Voice**
1. User clicks voice dropdown in toolbar
2. Dropdown shows categorized voices: "Online Voices" / "Offline Voices"
3. Each voice shows name, gender, accent, and a small [▶ Preview] button
4. Clicking Preview speaks a short sample sentence in that voice
5. Selecting a voice applies it immediately (or on next sentence boundary if reading)

**Flow 4: Adjusting Speed**
1. Speed control shows current rate (default: 1.0x)
2. Dropdown or slider offers: 0.5x, 0.75x, 1.0x, 1.25x, 1.5x, 1.75x, 2.0x
3. Speed change takes effect on the next sentence boundary (no mid-word distortion)
4. For edge-tts: uses the `--rate` parameter (e.g., "+25%" for 1.25x)
5. For piper-tts: adjusts `length_scale` in voice config
6. For pyttsx3: uses `setProperty('rate', ...)` 

**Flow 5: Settings**
1. Settings dialog opens as a modal
2. Tabs or sections:
   - **Voice:** Default engine preference, default voice, preview all voices
   - **Reading:** Default speed, sentence pause duration, skip headers/footers toggle
   - **Appearance:** Dark/Light/System theme, font size for document view, highlight color
   - **About:** Version, credits, links

### 4.5 Keyboard Shortcuts

| Action | Shortcut | Notes |
|---|---|---|
| Open file | `Ctrl+O` | Standard file open dialog |
| Play / Pause | `Space` | Toggle; most critical shortcut |
| Stop | `Escape` | Returns to beginning of document |
| Skip forward (next sentence) | `→` (Right Arrow) | Jump to next sentence |
| Skip backward (prev sentence) | `←` (Left Arrow) | Jump to previous sentence |
| Skip forward (next paragraph) | `Ctrl+→` | Larger jump |
| Skip backward (prev paragraph) | `Ctrl+←` | Larger jump |
| Increase speed | `Ctrl+↑` | Step up 0.25x |
| Decrease speed | `Ctrl+↓` | Step down 0.25x |
| Increase volume | `↑` (Up Arrow) | System volume or app volume |
| Decrease volume | `↓` (Down Arrow) | System volume or app volume |
| Toggle dark/light mode | `Ctrl+D` | Quick theme switch |
| Open settings | `Ctrl+,` | Standard settings shortcut |
| Open user guide | `F1` | Standard help shortcut |
| Quit | `Ctrl+Q` or `Alt+F4` | Graceful shutdown |

### 4.6 Drag and Drop

The entire application window should accept file drops. When a supported file is dragged over the window:
- The window border or background subtly changes to indicate "drop target active"
- On drop: file is loaded immediately
- On drop of an unsupported file type: brief toast notification saying "Unsupported format. Rhetor reads .pdf, .docx, .md, and .txt files."

CustomTkinter supports drag-and-drop via the `tkinterdnd2` extension. This must be bundled with the application.

---

## 5. Document Parsing — Detailed Specifications

### 5.1 PDF Parsing Strategy

PDFs are the most complex format to handle well. The parsing strategy must account for:

**Use PyMuPDF (`pymupdf`) for all PDF operations.**

- **Basic extraction:** `page.get_text("text")` with `sort=True` for reading-order text
- **Layout-aware extraction:** Use `pymupdf4llm.to_markdown()` for complex layouts — it handles multi-column, tables, headers/footers intelligently
- **Page-by-page processing:** Extract text per page, join with double newlines
- **Header/footer detection:** If text repeats identically on every page (or most pages), flag as header/footer and optionally skip
- **Table handling:** Tables extracted via PyMuPDF's table detection are read row-by-row, left-to-right. Announce "Table:" before reading tabular content.
- **Image-only PDFs:** Detect pages with no extractable text. Show a notification: "This page appears to be a scanned image. Text extraction requires OCR, which is not available in this version."
- **Encoding:** PyMuPDF handles Unicode natively; no special encoding work needed

### 5.2 DOCX Parsing Strategy

- **Use `python-docx`** to iterate `document.paragraphs` in order
- **Heading detection:** Check `paragraph.style.name` for Heading styles. Optionally announce heading level (e.g., pause slightly before headings, or say "Section:" before them)
- **Lists:** Detect numbered and bulleted lists via paragraph style. Read as sequential items.
- **Tables:** Iterate `document.tables`, read cell-by-cell in row order
- **Hyperlinks:** Extract link text only (ignore URLs for speech)
- **Footnotes/Endnotes:** Read inline if present in paragraph text
- **Embedded images:** Skip (cannot be read aloud). Optionally note "Image: [alt text]" if alt text exists.

### 5.3 Markdown Parsing Strategy

Markdown requires stripping formatting syntax while preserving semantic content:

- **Headers (`# ## ###`):** Strip `#` symbols, add a brief pause before header text
- **Bold/Italic (`**text**`, `*text*`):** Strip markers, read text normally
- **Links (`[text](url)`):** Read link text only, discard URL
- **Code blocks (``` ``` ```):** Read the code content but perhaps with a verbal cue: "Code block:" prefix
- **Inline code (`` ` ``):** Strip backticks, read normally
- **Lists (`- ` or `1. `):** Strip markers, read as sequential items with brief pauses
- **Blockquotes (`> `):** Strip `>`, optionally prefix with "Quote:"
- **Horizontal rules (`---`):** Translate to a longer pause
- **Images (`![alt](url)`):** Read alt text if present, skip otherwise
- **HTML tags in markdown:** Strip all HTML tags, read inner text

Implementation: use regex-based stripping (faster and more predictable than full AST parsing for this use case). The `markdown` library can be used to convert to HTML first, then `BeautifulSoup` or regex strips HTML to text — but direct regex on markdown syntax is simpler for MVP.

### 5.4 Plain Text Parsing Strategy

- **Encoding detection:** Use `charset-normalizer` to detect file encoding before reading
- **Fallback encoding chain:** UTF-8 → detected encoding → Latin-1 (Latin-1 never fails)
- **Line ending normalization:** Convert `\r\n` and `\r` to `\n`
- **Paragraph detection:** Two or more consecutive newlines indicate a paragraph break
- **Whitespace cleanup:** Collapse multiple spaces, strip leading/trailing whitespace per line

### 5.5 Text Processing Pipeline (All Formats)

After format-specific parsing produces clean text:

1. **Normalize whitespace** — collapse runs of spaces, normalize line endings
2. **Segment into sentences** — split on sentence-ending punctuation (`. ! ? `) followed by whitespace or newline. Handle abbreviations (Mr., Dr., U.S.) and decimal numbers (3.14) to avoid false splits. Use a simple heuristic: period followed by uppercase letter or newline = sentence boundary.
3. **Segment into paragraphs** — double newlines mark paragraph boundaries
4. **Build reading queue** — ordered list of `ReadingChunk` objects:
   ```
   ReadingChunk:
     text: str              # The sentence or fragment to speak
     paragraph_index: int   # Which paragraph this belongs to
     sentence_index: int    # Position within paragraph
     char_offset_start: int # Start position in full document text
     char_offset_end: int   # End position in full document text
     chunk_type: enum       # SENTENCE, HEADING, TABLE_ROW, CODE_BLOCK
   ```
5. **Estimate duration** — rough word count × average speaking rate gives estimated total reading time for the progress bar

---

## 6. TTS Engine Integration — Detailed Specifications

### 6.1 edge-tts Integration

```
Architecture:
  - edge-tts is fully async (uses aiohttp websockets)
  - Must run in a separate thread with its own asyncio event loop
  - Communication pattern:
    1. TTS Worker Thread receives text chunk from queue
    2. Creates edge_tts.Communicate(text, voice, rate)
    3. Iterates over communicate.stream() to get audio chunks
    4. Writes audio chunks to audio buffer queue
    5. Audio Player Thread reads from buffer and plays

Key parameters:
  - voice: str (e.g., "en-US-JennyNeural")
  - rate: str (e.g., "+25%" for 1.25x, "-30%" for 0.7x)
  - volume: str (e.g., "+0%")
  - pitch: str (e.g., "+0Hz")

Error handling:
  - Network timeout → retry once, then fall back to Tier 2
  - Voice not available → fall back to default voice
  - Service unavailable → fall back to Tier 2 with user notification

Streaming approach:
  - Process one sentence at a time
  - Pre-buffer: while current sentence plays, synthesize next 2-3 sentences
  - This provides gapless playback even with network latency
```

### 6.2 piper-tts Integration

```
Architecture:
  - Piper is synchronous and CPU-based
  - PiperVoice.load(model_path) loads the ONNX model
  - voice.synthesize_stream_raw(text) yields PCM audio chunks
  - Audio chunks are 16-bit signed integers at the model's sample rate

Voice model management:
  - Ship 2-3 models bundled with the installer (~50-150MB total)
  - Models stored in: <app_dir>/assets/voices/
  - Each model = .onnx file + .onnx.json config file
  - Voice catalog maps friendly names to model files

Speed control:
  - Modify length_scale in the .onnx.json config
  - Default is 1.0; higher = slower, lower = faster
  - 0.8 ≈ 1.25x speed, 0.67 ≈ 1.5x speed, 1.33 ≈ 0.75x speed

Audio format:
  - Raw PCM, sample rate defined in model config (typically 22050 Hz)
  - Must convert to format compatible with audio player
  - Use sounddevice or pygame for playback
```

### 6.3 pyttsx3 / SAPI5 Integration

```
Architecture:
  - pyttsx3 is synchronous and manages its own audio output
  - Wraps Windows SAPI5 (Speech API)
  - Has its own event loop (engine.runAndWait())

Integration approach:
  - Use pyttsx3's callbacks for word boundaries and utterance completion
  - engine.connect('started-word', callback) for position tracking
  - engine.connect('finished-utterance', callback) for completion

Speed control:
  - engine.setProperty('rate', words_per_minute)
  - Default is ~200 WPM; range 50-400 useful

Voice selection:
  - engine.getProperty('voices') returns installed SAPI5 voices
  - Typically includes: Microsoft David, Microsoft Zira, plus any
    additional voice packs the user has installed
  - Quality varies widely by installed voice pack

Caveat:
  - pyttsx3 handles its own audio output — cannot easily pipe through
    our audio player abstraction
  - Solution: use pyttsx3's save_to_file() to generate WAV, then play
    through our audio pipeline for consistency
  - OR: let pyttsx3 handle playback directly in SAPI fallback mode
    (simpler for MVP, accept the inconsistency)
```

### 6.4 Voice Catalog Design

The voice selector UI shows a curated, friendly list — not raw engine IDs:

```json
{
  "voices": [
    {
      "id": "jenny-us",
      "display_name": "Jenny",
      "description": "Warm and professional",
      "gender": "Female",
      "accent": "American",
      "engine": "edge-tts",
      "engine_voice_id": "en-US-JennyNeural",
      "requires_internet": true,
      "preview_text": "Hello! I'm Jenny, and I'll be reading your document today."
    },
    {
      "id": "amy-offline",
      "display_name": "Amy (Offline)",
      "description": "Clear and natural",
      "gender": "Female",
      "accent": "American",
      "engine": "piper",
      "engine_voice_id": "en_US-amy-medium",
      "requires_internet": false,
      "preview_text": "Hello! I'm Amy, available even without an internet connection."
    }
  ]
}
```

---

## 7. Built-In User Guide

### 7.1 Delivery Method

The user guide is a markdown file (`assets/user_guide.md`) bundled with the application. It is displayed in a dedicated window using a styled text widget within CustomTkinter. The guide is rendered with basic formatting (headings, bold, lists) — not a full markdown renderer, but enough to be readable and attractive.

Access points:
- **F1** key from anywhere in the app
- **Help** button in the toolbar
- **"Read User Guide"** link on the Welcome Screen
- **Help → User Guide** in the menu bar

### 7.2 User Guide Content Outline

```markdown
# Rhetor User Guide

## Welcome to Rhetor
Brief intro, what the app does, supported formats.

## Getting Started
- Opening your first document (Open button, drag-and-drop, File menu)
- Pressing Play to start reading
- Basic controls walkthrough

## Playback Controls
- Play / Pause (Space bar)
- Stop (Escape)
- Skip forward and backward (arrow keys)
- Speed adjustment
- Volume control

## Choosing a Voice
- Online voices vs. Offline voices
- How to preview a voice
- Setting a default voice
- What happens when you're offline

## Supported Document Formats
- PDF files — what works well, limitations with scanned/image PDFs
- Word documents (.docx) — headings, lists, tables
- Markdown files (.md) — how formatting is handled
- Text files (.txt) — encoding support

## Settings
- Appearance (Dark/Light mode, font size)
- Voice preferences
- Reading preferences (speed, pauses)

## Keyboard Shortcuts
Full table of all shortcuts.

## Troubleshooting
- "No audio is playing" — check volume, check voice engine
- "Voice sounds robotic" — switch from offline to online voice
- "PDF text is garbled" — document may be scanned/image-based
- "App can't connect for online voices" — check internet, or use offline

## About Rhetor
- Version info
- Credits and acknowledgments
- Built by High Velocity Solutions LLC
- Contact/feedback information
```

### 7.3 User Guide UX Details

- The guide window opens as a **non-modal top-level window** (user can read guide while the app is open behind it)
- Guide has its own search/find feature (`Ctrl+F` within the guide)
- Guide sections are navigable via a sidebar table of contents
- The guide itself can optionally be read aloud by Rhetor (meta, but useful for accessibility — a "Read this guide aloud" button)

---

## 8. Settings & Persistence

### 8.1 Settings Schema

```json
{
  "version": "1.0",
  "appearance": {
    "theme": "system",
    "font_size": 14,
    "highlight_color": "#d4a843",
    "window_width": 900,
    "window_height": 700,
    "window_x": null,
    "window_y": null
  },
  "voice": {
    "preferred_engine": "auto",
    "preferred_voice_id": "jenny-us",
    "offline_voice_id": "amy-offline",
    "force_offline": false
  },
  "reading": {
    "speed": 1.0,
    "volume": 0.8,
    "pause_between_paragraphs_ms": 500,
    "pause_between_sentences_ms": 100,
    "announce_headings": true,
    "skip_repeated_headers": true
  },
  "recent_files": [
    "C:\\Users\\AJ\\Documents\\report.pdf",
    "C:\\Users\\AJ\\Documents\\notes.md"
  ]
}
```

### 8.2 Persistence Behavior

- Settings saved to `%APPDATA%\Rhetor\settings.json`
- Settings are loaded on app start; defaults used if file doesn't exist or is corrupted
- Settings are saved on change (not on exit — prevents loss if app crashes)
- Window position and size are saved on close and restored on open
- Recent files list: last 10 files, shown in File menu and optionally on Welcome Screen

---

## 9. Packaging & Distribution

### 9.1 Build Pipeline

**Tool: PyInstaller (one-directory mode recommended for MVP)**

One-directory mode is preferred over one-file because:
- Faster startup (no temp extraction)
- Easier to debug
- Piper voice models (50-150MB) don't need to be extracted to temp on every launch
- The installer wraps the directory into a clean install anyway

```powershell
# Build command (conceptual)
pyinstaller --name Rhetor `
  --icon build/rhetor.ico `
  --windowed `
  --add-data "assets;assets" `
  --add-data "assets/voices;assets/voices" `
  --hidden-import pyttsx3.drivers `
  --hidden-import pyttsx3.drivers.sapi5 `
  rhetor/main.py
```

### 9.2 Installer

**Tool: Inno Setup (free, well-proven, widely trusted)**

The installer should:
- Show the Rhetor branding/logo on install screens
- Allow choosing install directory
- Create Start Menu shortcut
- Create optional Desktop shortcut
- Register `.rhetor` file association (future: double-click to open documents in Rhetor)
- Set up uninstaller
- Total installed size estimate: ~200-350MB (Python runtime + Qt/Tk + Piper models + PyMuPDF)

### 9.3 Estimated Bundle Size

| Component | Approximate Size |
|---|---|
| Python 3.11 runtime | ~30 MB |
| CustomTkinter + Tkinter | ~15 MB |
| PyMuPDF | ~30 MB |
| edge-tts | <1 MB |
| piper-tts + ONNX Runtime | ~50 MB |
| Piper voice models (2-3 medium) | ~50-100 MB |
| python-docx, pyttsx3, others | ~10 MB |
| pygame | ~15 MB |
| App code + assets | ~5 MB |
| **Total estimated** | **~200-260 MB installed** |

### 9.4 System Requirements

- **OS:** Windows 10 or later (64-bit)
- **RAM:** 4 GB minimum, 8 GB recommended
- **Disk:** 500 MB free for installation
- **Audio:** Any audio output device (speakers, headphones, Bluetooth)
- **Internet:** Optional (required for online neural voices)
- **CPU:** Any modern x86_64 processor (no GPU required)

---

## 10. Quality Assurance Plan

### 10.1 Testing Strategy

| Test Type | Scope | Tools |
|---|---|---|
| **Unit tests** | Parsers, text processor, settings, voice catalog | pytest |
| **Integration tests** | Document → parsed text → TTS → audio pipeline | pytest + mocking |
| **Manual UX testing** | Full user flows on Windows 10 and 11 | Checklist-driven |
| **Format testing** | Sample files for each format with edge cases | Fixture files |
| **Voice testing** | Each curated voice speaks sample text correctly | Manual + recording |
| **Performance testing** | Large documents (100+ pages PDF), startup time | Manual timing |
| **Accessibility testing** | Keyboard navigation, screen reader compatibility | Manual |

### 10.2 Test Document Matrix

| Scenario | Format | Tests |
|---|---|---|
| Simple text, few paragraphs | .txt | Baseline reading |
| Unicode content (accents, CJK) | .txt | Encoding detection |
| Multi-heading document | .md | Heading detection, stripping |
| Code blocks in markdown | .md | Code reading behavior |
| Simple Word document | .docx | Basic paragraph extraction |
| Word doc with tables | .docx | Table reading order |
| Word doc with images | .docx | Image skipping |
| Simple PDF | .pdf | Basic text extraction |
| Multi-column PDF | .pdf | Column reading order |
| Scanned/image PDF | .pdf | Graceful failure notification |
| PDF with tables | .pdf | Table detection and reading |
| Very large document (200+ pages) | .pdf | Performance, memory usage |
| Empty file | all | Graceful "nothing to read" message |
| Password-protected PDF | .pdf | Graceful error message |
| Corrupted file | all | Graceful error handling |

---

## 11. Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Microsoft changes/blocks edge-tts access | High — primary voice quality | Medium | Tiered engine architecture ensures offline fallback. Monitor edge-tts GitHub for changes. |
| Piper voice quality deemed insufficient | Medium — offline UX | Low | Ship medium-quality models; high-quality models available as optional download. |
| PyInstaller bundling issues with ONNX Runtime | Medium — blocks release | Medium | Test bundling early and often. Pin versions. Maintain working .spec file. |
| Complex PDFs extract garbled text | Medium — user frustration | Medium | Use PyMuPDF's layout-aware extraction. Show "text quality may vary" for complex PDFs. |
| Large files cause UI freeze | High — app feels broken | Low (if threading done right) | Strict threading model. Load and parse in background thread. Never block UI thread. |
| CustomTkinter limitations hit for advanced UI needs | Low — MVP is simple enough | Low | CustomTkinter handles MVP scope well. PySide6 migration path exists for v2. |
| Audio playback gaps between sentences | Medium — breaks immersion | Medium | Pre-buffering strategy: synthesize 2-3 sentences ahead. Tune buffer size. |

---

## 12. Future Roadmap (Post-MVP)

### v1.1 — Enhanced Reading
- Bookmark positions, resume where you left off
- Export to MP3/WAV audio file
- EPUB and HTML support
- Recent files quick-access panel
- "Read selected text" mode (highlight a portion, read only that)

### v1.2 — Power Features
- Batch reading queue (load multiple documents)
- Chapter/section navigation for structured documents
- Reading statistics (words read, time spent)
- Custom pronunciation dictionary (override how specific words are spoken)

### v2.0 — Platform Evolution
- Migrate to PySide6 for richer UI capabilities
- Voice cloning integration (clone your own voice to read documents)
- AI-powered summarization before reading
- Cloud sync of reading positions and preferences
- Plugin system for additional document formats

---

## 13. Development Milestones

| Phase | Duration | Deliverables |
|---|---|---|
| **Phase 1: Foundation** | Week 1-2 | Project scaffolding, document parsers for all 4 formats, text processing pipeline, unit tests for parsers |
| **Phase 2: TTS Integration** | Week 2-3 | edge-tts engine wrapper, piper-tts engine wrapper, pyttsx3 fallback, engine manager with failover logic, voice catalog |
| **Phase 3: Audio Pipeline** | Week 3-4 | Audio player with threading, pre-buffering, playback controls (play/pause/stop/skip), gapless playback |
| **Phase 4: UI Build** | Week 4-5 | CustomTkinter main window, document view with highlighting, playback controls widget, voice selector, settings dialog, welcome screen |
| **Phase 5: User Guide & Polish** | Week 5-6 | Built-in user guide, keyboard shortcuts, drag-and-drop, error handling, edge case testing |
| **Phase 6: Package & Ship** | Week 6-7 | PyInstaller bundling, Inno Setup installer, final testing on clean Windows 10/11 VMs, documentation |

**Total estimated MVP timeline: 6-7 weeks**

---

*This document serves as the complete blueprint for building Rhetor. Every section is designed to be actionable — a developer (or Claude) should be able to pick up any section and begin implementation with confidence.*

*Built with care by AJ Geddes and Claude — High Velocity Solutions LLC, March 2026*
