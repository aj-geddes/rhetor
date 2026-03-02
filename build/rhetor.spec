# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Rhetor — one-directory windowed application."""

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('src/assets', 'assets'),
    ],
    hiddenimports=[
        'pyttsx3.drivers',
        'pyttsx3.drivers.sapi5',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'test',
        'tests',
        'pytest',
        'mypy',
        'ruff',
    ],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Rhetor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Rhetor',
)
