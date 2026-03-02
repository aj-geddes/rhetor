#!/usr/bin/env bash
# build.sh — Build Rhetor.exe from WSL2 using Windows Python + PyInstaller.
#
# Usage:  bash build/build.sh
# Run from the project root (where pyproject.toml lives).

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────

WIN_PYTHON="/mnt/c/Python313/python.exe"
BUILD_DIR="/mnt/c/Users/Munso/rhetor-app"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Convert WSL path to Windows path for Windows executables.
# /mnt/c/Users/Munso/rhetor-app -> C:\Users\Munso\rhetor-app
wsl_to_win() {
    local p="$1"
    # Extract drive letter from /mnt/X/...
    local drive="${p:5:1}"
    local rest="${p:6}"
    echo "${drive^^}:${rest//\//\\}"
}

WIN_BUILD_DIR="$(wsl_to_win "$BUILD_DIR")"

# ── Preflight checks ────────────────────────────────────────────────────────

if [[ ! -x "$WIN_PYTHON" ]]; then
    echo "ERROR: Windows Python not found at $WIN_PYTHON"
    echo "       Install Python 3.13 on Windows or update WIN_PYTHON in this script."
    exit 1
fi

if [[ ! -f "$PROJECT_ROOT/pyproject.toml" ]]; then
    echo "ERROR: Run this script from the project root (where pyproject.toml lives)."
    exit 1
fi

echo "=== Rhetor Build ==="
echo "  Project root : $PROJECT_ROOT"
echo "  Build dir    : $BUILD_DIR"
echo "  Windows path : $WIN_BUILD_DIR"
echo "  Windows Python: $WIN_PYTHON"
echo ""

# ── Step 1: Create build directory ───────────────────────────────────────────

echo "[1/5] Preparing build directory..."
mkdir -p "$BUILD_DIR"

# ── Step 2: Sync source files ────────────────────────────────────────────────

echo "[2/5] Syncing source to $BUILD_DIR/src/ ..."
rsync -a --delete \
    --exclude='.venv/' \
    --exclude='__pycache__/' \
    --exclude='.git/' \
    --exclude='tests/' \
    --exclude='build/' \
    --exclude='.mypy_cache/' \
    --exclude='.pytest_cache/' \
    --exclude='.ruff_cache/' \
    --exclude='*.pyc' \
    --exclude='dist/' \
    "$PROJECT_ROOT/" "$BUILD_DIR/src/"

# Copy spec file into build dir (PyInstaller reads it from there)
cp "$PROJECT_ROOT/build/rhetor.spec" "$BUILD_DIR/rhetor.spec"

# ── Step 3: Generate requirements.txt and set up venv ────────────────────────

echo "[3/5] Setting up Windows venv and installing dependencies..."

# Generate requirements.txt from pyproject.toml dependencies
cat > "$BUILD_DIR/requirements.txt" <<'REQS'
pymupdf>=1.24.0
python-docx>=1.1.0
charset-normalizer>=3.3.0
edge-tts>=7.2.0
piper-tts>=1.4.0
pyttsx3>=2.90
pygame>=2.5.0
customtkinter>=5.2.0
REQS

# Create venv if it doesn't exist (Windows Python needs Windows-style path)
if [[ ! -d "$BUILD_DIR/.venv" ]]; then
    "$WIN_PYTHON" -m venv "$WIN_BUILD_DIR\\.venv"
fi

VENV_PYTHON="$BUILD_DIR/.venv/Scripts/python.exe"
PYINSTALLER="$BUILD_DIR/.venv/Scripts/pyinstaller.exe"

"$VENV_PYTHON" -m pip install --upgrade pip --quiet
"$VENV_PYTHON" -m pip install -r "$WIN_BUILD_DIR\\requirements.txt" pyinstaller --quiet

# ── Step 4: Run PyInstaller ──────────────────────────────────────────────────

echo "[4/5] Running PyInstaller..."
cd "$BUILD_DIR"
"$PYINSTALLER" --noconfirm "$WIN_BUILD_DIR\\rhetor.spec"

# ── Step 5: Report results ───────────────────────────────────────────────────

EXE_PATH="$BUILD_DIR/dist/Rhetor/Rhetor.exe"

echo ""
echo "[5/5] Build complete!"
if [[ -f "$EXE_PATH" ]]; then
    echo "  SUCCESS: $EXE_PATH"
    echo ""
    echo "  To launch:  $EXE_PATH"
    # Show size
    SIZE=$(du -sh "$BUILD_DIR/dist/Rhetor/" | cut -f1)
    echo "  Bundle size: $SIZE"
else
    echo "  ERROR: Rhetor.exe not found at $EXE_PATH"
    echo "  Check PyInstaller output above for errors."
    exit 1
fi
