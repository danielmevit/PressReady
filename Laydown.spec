# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — one spec for Windows, macOS and Linux.

PyInstaller cannot cross-compile: each platform's artifact has to be built on that
platform, which is why the release workflow runs a job per OS rather than building
everything here. This file only handles what differs *per platform*: the icon format
and the macOS .app bundle.

Run via the packaging scripts (packaging/<os>/build.*), not directly, so the version
and output names come from laydown/__init__.py.
"""

import os
import sys

from PyInstaller.utils.hooks import collect_submodules

sys.path.insert(0, os.path.abspath("."))
from laydown import __version__  # noqa: E402

IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"

# Windows wants .ico, macOS wants .icns, Linux ships the PNGs and uses a .desktop file.
if IS_WIN:
    icon = "assets/icons/laydown.ico"
elif IS_MAC:
    icon = "assets/icons/laydown.icns" if os.path.exists(
        "assets/icons/laydown.icns") else None
else:
    icon = None

a = Analysis(
    ["laydown/__main__.py"],
    pathex=[],
    binaries=[],
    datas=[("assets/icons", "assets/icons")],
    hiddenimports=["fitz", "fitz.fitz", *collect_submodules("PyQt6")],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter", "matplotlib", "numpy", "scipy", "pandas", "PIL",
        "IPython", "notebook", "pytest", "pytest_qt",
        # Qt modules the app never touches — each is tens of MB.
        "PyQt6.QtWebEngineCore", "PyQt6.QtWebEngineWidgets", "PyQt6.QtQuick",
        "PyQt6.QtQml", "PyQt6.Qt3DCore", "PyQt6.QtMultimedia", "PyQt6.QtBluetooth",
        "PyQt6.QtCharts", "PyQt6.QtDataVisualization", "PyQt6.QtSql",
        "PyQt6.QtTest", "PyQt6.QtNetworkAuth", "PyQt6.QtPositioning",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Laydown",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX mangles Qt libraries on macOS and is not worth the risk on Linux either.
    upx=IS_WIN,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=IS_MAC,   # lets Finder "open with" pass the PDF path through
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=IS_WIN,
    upx_exclude=[],
    name="Laydown",
)

if IS_MAC:
    app = BUNDLE(
        coll,
        name="Laydown.app",
        icon=icon,
        bundle_identifier="xyz.damt.laydown",
        version=__version__,
        info_plist={
            "CFBundleShortVersionString": __version__,
            "CFBundleVersion": __version__,
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
            "CFBundleDocumentTypes": [{
                "CFBundleTypeName": "PDF document",
                "CFBundleTypeRole": "Editor",
                "LSItemContentTypes": ["com.adobe.pdf"],
                "LSHandlerRank": "Alternate",
            }],
        },
    )
