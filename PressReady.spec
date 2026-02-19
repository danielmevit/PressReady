# -*- mode: python ; coding: utf-8 -*-
# PressReady v2 — PyInstaller spec file (one-dir mode)

import os, sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect PyQt6 submodules so nothing is missed
pyqt6_hiddens = collect_submodules("PyQt6")

a = Analysis(
    ["pressready/__main__.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("assets/icons", "assets/icons"),
    ],
    hiddenimports=[
        "fitz",
        "fitz.fitz",
        *pyqt6_hiddens,
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "numpy",
        "scipy",
        "pandas",
        "PIL",
        "IPython",
        "notebook",
        "pytest",
        "pytest_qt",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PressReady",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icons/pressready.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="PressReady",
)
