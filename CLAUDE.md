# Rhetor — Project Conventions

## Overview
Rhetor is a Windows desktop document reader that reads documents aloud using TTS.
Python >=3.10, <3.13.

## Project Structure
- `core/` — Business logic (zero UI imports). Parsers, text processing, reading session.
- `core/parsers/` — Format-specific document parsers (text, markdown, docx, pdf).
- `tts/` — Text-to-speech engine abstraction (Phase 2).
- `audio/` — Audio playback management (Phase 3).
- `ui/` — All UI components using CustomTkinter (Phase 4).
- `tests/` — Test suite. Fixtures are generated programmatically, not committed as binaries.
- `build/` — Build and packaging configuration.
- `assets/` — Static resources (icons, fonts, voices, user guide).

## Code Style
- Formatter/linter: `ruff` (line length 99, target py310)
- Type checker: `mypy` (strict — disallow_untyped_defs)
- Tests: `pytest`
- Use frozen dataclasses with `__slots__` for data models
- Use Protocol (not ABC) for structural subtyping
- Import sorting: isort-compatible via ruff

## Commands
- Install dev: `pip install -e ".[dev]"`
- Run tests: `python -m pytest -v`
- Lint: `ruff check .`
- Type check: `mypy .`

## Conventions
- `core/` must never import from `ui/`, `tts/`, or `audio/`
- All parsers implement the `BaseParser` Protocol from `core/parsers/__init__.py`
- ReadingChunk is frozen/immutable for thread safety
- Settings stored as JSON at platform-appropriate config dir
