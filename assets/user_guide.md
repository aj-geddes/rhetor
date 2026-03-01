# Rhetor User Guide

Welcome to **Rhetor** — The Master Orator for Your Documents.

Rhetor reads your documents aloud using high-quality text-to-speech, letting you listen to content hands-free.

---

## Getting Started

1. Launch Rhetor.
2. Open a document via **File > Open** or press **Ctrl+O**.
3. Press **Space** to begin reading.

### Supported Formats

- **Plain Text** (.txt) — any encoding, auto-detected
- **Markdown** (.md) — headings, lists, and formatting extracted
- **Word Documents** (.docx) — paragraphs, headings, and tables
- **PDF Documents** (.pdf) — text extracted page by page

You can also drag and drop a file onto the Rhetor window to open it.

---

## Playback Controls

Use the toolbar buttons or keyboard shortcuts:

| Action | Button | Shortcut |
|--------|--------|----------|
| Play / Pause | Play | Space |
| Stop | Stop | Escape |
| Previous Chunk | << | Left Arrow |
| Next Chunk | >> | Right Arrow |
| Previous Paragraph | — | Ctrl+Left |
| Next Paragraph | — | Ctrl+Right |

---

## Keyboard Shortcuts

### Navigation

| Shortcut | Action |
|----------|--------|
| Ctrl+O | Open a document |
| Ctrl+Q | Quit Rhetor |
| F1 | Open this User Guide |
| Ctrl+, | Open Settings |

### Playback

| Shortcut | Action |
|----------|--------|
| Space | Play / Pause |
| Escape | Stop playback |
| Left Arrow | Previous chunk (sentence) |
| Right Arrow | Next chunk (sentence) |
| Ctrl+Left | Previous paragraph |
| Ctrl+Right | Next paragraph |

### Adjustment

| Shortcut | Action |
|----------|--------|
| Ctrl+Up | Increase speed (+0.25x) |
| Ctrl+Down | Decrease speed (-0.25x) |
| Up Arrow | Increase volume (+5%) |
| Down Arrow | Decrease volume (-5%) |
| Ctrl+D | Toggle dark/light theme |

---

## Voice & Speed

### Selecting a Voice

Use the **Voice** dropdown in the toolbar to choose from available voices. Rhetor includes three tiers of TTS engines:

1. **Edge TTS** (online) — Natural-sounding neural voices. Requires an internet connection.
2. **Piper TTS** (offline) — High-quality offline voices using neural models. Works without internet.
3. **SAPI** (offline, Windows) — Built-in Windows voices. Always available as a fallback.

Rhetor automatically falls back to the next tier if the preferred engine is unavailable.

### Adjusting Speed

Use the **Speed** slider (0.5x to 2.0x) or press **Ctrl+Up** / **Ctrl+Down** to adjust in 0.25x steps.

### Adjusting Volume

Use the **Volume** slider (0% to 100%) or press **Up** / **Down** arrow keys to adjust in 5% steps.

---

## Settings

Open settings via **File > Settings** or press **Ctrl+,**.

### Appearance Tab

- **Theme** — Choose System, Dark, or Light mode.
- **Font Size** — Adjust the document display font size.
- **Highlight Color** — Change the color used to highlight the current chunk.

### Voice Tab

- **Preferred Engine** — Choose your default TTS engine.
- **Preferred Voice** — Select a default voice.
- **Force Offline** — Disable online voices for offline-only operation.

### Reading Tab

- **Speed** — Default playback speed.
- **Volume** — Default playback volume.
- **Paragraph Pause** — Duration of pause between paragraphs (ms).
- **Sentence Pause** — Duration of pause between sentences (ms).

---

## Drag and Drop

You can drag a supported file directly onto the Rhetor window to open it. The window will highlight to indicate it is ready to accept the file. If the file format is not supported, the status bar will show an error message.

---

## Troubleshooting

**No audio output**
- Check that your system volume is not muted.
- Ensure pygame is installed correctly.
- Try selecting a different voice from the dropdown.

**Robotic or low-quality voice**
- You may be using the SAPI fallback engine. Switch to Edge TTS (requires internet) or install Piper voice models for better offline quality.

**Garbled PDF text**
- Some PDFs contain scanned images rather than selectable text. Rhetor can only read PDFs with embedded text.
- PDFs with unusual fonts or encodings may not extract cleanly.

**Voices not loading**
- Wait a moment — voice initialization happens in the background on startup.
- Check the status bar for engine status information.

**Working offline**
- Enable **Force Offline** in Settings > Voice to avoid timeouts when no internet is available.
- Piper and SAPI voices work without an internet connection.

---

## About Rhetor

**Rhetor** — The Master Orator for Your Documents

Created by High Velocity Solutions LLC.

Press **F1** at any time to open this guide.
