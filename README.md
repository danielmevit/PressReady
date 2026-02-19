# PressReady v2 — Professional PDF Imposition Tool

## What Is This?

PressReady v2 is a complete rewrite of PressReady, inspired by the professional
workflow of **Imposition Wizard 3** (Appsforlife). It is a standalone desktop app
for imposing PDF pages onto press sheets for commercial printing.

Built with **Python 3.10+**, **PyQt6**, and **PyMuPDF (fitz)**.

---

## Installers

| Format | File | Use case |
|--------|------|----------|
| **MSIX** | `PressReady_2.0.0.msix` | Standard Windows installer — double-click to install. Integrates with Start Menu, Settings → Apps, and Add/Remove Programs. Clean install/uninstall. |
| **Portable ZIP** | `PressReady_2.0.0-windows-x64.zip` | Extract anywhere and run `PressReady.exe`. No installation required. Ideal for USB drives, portable use, or environments where you can't install apps. |

Both are produced by `build_msix.ps1` and placed in `installer_output/`.

---

## Architecture: 4-Tab Model

The UI mirrors the proven 4-tab workflow used by professional imposition tools:

| Tab | Purpose |
|-----|---------|
| **Preprocessors** | Transform source pages before imposition (rotate, scale, reorder, clone, split, setup bleeds) |
| **Layout** | Choose imposition layout: N-Up (2/4/6/8), Booklet (saddle-stitch), with gutters, signatures, page creep |
| **Sheet** | Define output sheet: size presets (A4/A3/Letter/Tabloid/Custom), margins (per-side), orientation, duplex |
| **Marks** | Add print marks: crop marks, trim lines, registration (star/bull-eye), folding marks, text labels, color bars |

---

## Current Status

### Session 1 — 2026-02-19

**What was done:**
- Analyzed Imposition Wizard 3 installation (`C:\Program Files\Appsforlife\Imposition Wizard 3`).
  It's a Qt/QML C++ app — compiled binaries, no readable source. Used UI screenshots
  to reverse-engineer the full data model and parameter set.
- Created `pressready/engine/data_model.py` with enums and dataclasses matching all
  4 tabs: PreprocessorType, LayoutSettings (with Booklet modes, signatures, creep),
  SheetSettings, MarkType.
- Created v2 directory structure as a clean rewrite.
- Ported and enhanced the v1 imposition engine (N-Up + Booklet).
- Built full 4-tab PyQt6 UI with live preview panel.

**Working features (v2.0.0):**
- [x] 4-tab UI: Preprocessors, Layout, Sheet, Marks
- [x] File load via button or drag-and-drop
- [x] Preprocessors: Rotate Pages, Scale Pages, Reorder Pages
- [x] Layout: N-Up (2-up, 4-up), Booklet (saddle-stitch sheetwise)
- [x] Layout: Gutters (horizontal/vertical), Page range selection
- [x] Sheet: Size presets (A4, A3, Letter, Tabloid, Custom), per-side margins, orientation
- [x] Marks: Crop marks, Registration marks, Trim lines, Folding marks, Text labels
- [x] Live source + imposed sheet preview with page/sheet navigation
- [x] Background PDF export with progress dialog
- [x] Vector placement (no rasterization) via PyMuPDF show_pdf_page

### Session 2 — 2026-02-19 (continued)

**What was done:**
- Added **menu bar** (File, Edit, View, Help) modeled after Imposition Wizard 3.
- **File menu:** Open PDF (Ctrl+O), Open Recent (persists across sessions via QSettings),
  Close PDF (Ctrl+F4), Generate PDF (Ctrl+G), Settings dialog (placeholder), Quit.
- **Edit menu:** Undo/Redo placeholders, Select All.
- **View menu:** Zoom In/Out/Reset (Ctrl++/−/0) — changes preview DPI (60–300).
  Checkable toggles: Show Page Numbers, Show Page Frames, Show Page Previews.
- **Help menu:** Tutorials (F1) — opens a full embedded HTML documentation dialog
  covering every tab, parameter, mark type, and keyboard shortcut.
  Open System Folder, About dialog.
- **Title bar** now shows the loaded file name (e.g. "PressReady v2 — brochure.pdf").
- Added `clear_all()` and `set_dpi()` to PreviewPanel to support Close PDF and Zoom.
- Created comprehensive tutorials/reference documentation as embedded HTML
  (accessible via Help → Tutorials or F1).

### Session 3 — 2026-02-19 (continued)

**What was done:**
- **Major UI restructure** — two-column layout matching Imposition Wizard 3:
  - **Left column:** Icon toolbar (view modes, zoom/fit, Generate PDF) + scrollable
    multi-sheet preview canvas showing ALL imposed sheets in a grid.
  - **Right column:** Icon-only tab bar (Preprocessors, Layout, Sheet, Marks) +
    active tab heading + scrollable tab content. Extends full height from menu bar
    to status bar.
- **Multi-sheet canvas** replaces old side-by-side source/sheet preview.
  All imposed sheets render at 72 DPI in a background worker and display in
  a configurable 1/2/4-column grid with zoom, fit-to-width/page, and actual-size.
- **Custom-drawn toolbar icons** via QPainter (column layout, zoom in/out,
  fit-to-width, fit-to-page, 1:1 actual size). No external icon assets needed.
- **Icon tab bar** with custom-drawn icons for each settings tab (overlapping pages,
  2×2 grid, ruled page, gear cog). Tooltip on hover, bold heading on selection.
- **Dark mode** — comprehensive dark theme across the entire application:
  - Background palette: `#1e1e1e` (canvas), `#252526` (settings panel), `#2d2d2d`
    (toolbar/menu), `#3c3c3c` (inputs).
  - Global Qt stylesheet covering all widget types: menus, inputs, buttons,
    checkboxes, group boxes, lists, scrollbars, tooltips, progress bars, dialogs.
  - Tutorials documentation also themed dark.
- **Orange accent color** (`#D07B24`) replaces blue throughout: Generate PDF button,
  active tab indicator, menu hover, input focus borders, checked checkboxes,
  group box titles, progress bar, documentation headings.
- **Toolbar centering** — zoom/fit icons are centered between the column-view
  buttons (left) and Generate PDF button (right).
- View overlay toggles (page tops/numbers/frames/previews) now work across
  all sheets in the multi-sheet canvas.

### Session 4 — 2026-02-19 (continued)

**What was done:**
- **App icon** — designed custom PressReady logo (orange PR monogram with rounded
  corners). Converted from 1024×1024 source to all standard sizes (16, 24, 32, 48,
  64, 128, 256) plus a multi-size `pressready.ico` for installer use.
  Stored in `assets/icons/`.
- Icon wired into the app via `setWindowIcon` on both `QApplication` and `QMainWindow`.
  Windows taskbar grouping set via `SetCurrentProcessExplicitAppUserModelID`.
- **Repo restructured** — `v2/` promoted to project root as the main application.
  Original v1 code archived to `_legacy/v1/`. GitHub repo updated.
- **Accent color darkened** from `#E8912D` to `#D07B24` with adjusted hover/pressed
  states (`#BC6F20` / `#A8631C`) across all UI elements.

**Not yet implemented (planned):**
- [ ] Preprocessors: Clone Pages, N+1 Pages, Split Pages, Shuffle, Override Box, Setup Bleeds, Center & Crop, Slice, Script
- [ ] Layout: Work-and-Turn, Work-and-Tumble, Perfect Bound modes
- [ ] Layout: 6-Up, 8-Up, custom grid
- [ ] Layout: Signatures (multi-section booklets), Page Creep compensation
- [ ] Layout: Right-to-left, Move fillers to middle
- [ ] Marks: Gap Crop Marks, Perforation Marks, Color Bars (Auto/PDF), Star Target, Bull Eye, Barcode, Plate Names, Collating Marks, Angle Mark, Custom Mark
- [ ] Sheet: Duplex mode, per-sheet rotation
- [ ] Presets system (save/load imposition profiles)
- [ ] Undo/Redo for settings
- [ ] Settings dialog (default sheet size, DPI, export options)
- [ ] Batch processing, Hot Folders
- [x] View toggles wired to preview (page numbers, frames, tops, previews) — done in Session 2–3

---

## Project Structure

```
PressReady/
├── pressready/                    # ← main application (v2)
│   ├── __init__.py
│   ├── __main__.py                # Entry point
│   ├── engine/
│   │   ├── data_model.py          # Enums + dataclasses for all settings
│   │   ├── utils.py               # mm↔pt conversion, page range parsing
│   │   ├── preprocessors.py       # Page transforms (rotate, scale, reorder)
│   │   ├── impose.py              # N-Up + Booklet imposition engine
│   │   └── marks.py               # Crop marks, registration, folding, labels
│   └── ui/
│       ├── main_window.py         # Main window (dark theme, two-column layout)
│       ├── preprocessors_tab.py   # Preprocessors tab UI
│       ├── layout_tab.py          # Layout tab UI
│       ├── sheet_tab.py           # Sheet tab UI
│       ├── marks_tab.py           # Marks tab UI
│       └── preview_panel.py       # Multi-sheet scrollable preview canvas
├── assets/icons/                  # App icons (PNG + ICO + msix/)
├── tests/
├── _legacy/v1/                    # Original v1 code (archived)
├── PressReady.spec                # PyInstaller build spec
├── AppxManifest.xml               # MSIX package manifest
├── build_msix.ps1                 # Builds .msix + portable .zip
├── pyproject.toml
├── CHANGELOG.md                   # Release notes
├── installer_output/              # Built installers (gitignored)
│   ├── PressReady_2.0.0.msix     # MSIX installer
│   └── PressReady_2.0.0-windows-x64.zip  # Portable
└── README.md                      ← you are here
```

## Running

```bash
cd "D:\Vibe Coding\PressReady"
pip install PyQt6 PyMuPDF
python -m pressready
```

## Building the Windows Installer (MSIX)

The build pipeline uses **PyInstaller** to bundle the app, then **Windows SDK** tools
to create a native **MSIX** package — the standard Windows installer format.
No third-party installer tools are needed.

### Prerequisites

- Python 3.10+ with `PyQt6` and `PyMuPDF` installed
- [PyInstaller](https://pyinstaller.org/) — `pip install pyinstaller`
- Windows 10 SDK — `winget install Microsoft.WindowsSDK.10.0.26100` (free, provides `makeappx.exe` and `signtool.exe`)

### One-command build

```powershell
powershell -ExecutionPolicy Bypass -File build_msix.ps1
```

This runs all five steps automatically:
1. **PyInstaller** bundles the app into `dist/PressReady/`
2. Creates a **self-signed certificate** (first run only, stored in `certs/`)
3. Stages the MSIX contents (exe + manifest + icons)
4. Packages and signs → `installer_output/PressReady_2.0.0.msix`
5. Creates portable ZIP → `installer_output/PressReady_2.0.0-windows-x64.zip`

Use `-SkipPyInstaller` to skip step 1 if you already have a fresh build in `dist/`.

### First-time certificate trust (one-time, requires admin)

Before the MSIX can be installed, the signing certificate must be trusted.
Run this **once** in an elevated PowerShell:

```powershell
Import-Certificate -FilePath "certs\PressReady.cer" -CertStoreLocation Cert:\LocalMachine\TrustedPeople
```

### Installing the MSIX

Double-click `PressReady_2.0.0.msix` to install via the standard Windows UI, or:

```powershell
Add-AppxPackage -Path installer_output\PressReady_2.0.0.msix
```

The installed app:
- Appears in the **Start Menu** and Windows Search
- Shows in **Settings → Apps** with a proper uninstall option
- Registers as a handler for `.pdf` files
- Updates cleanly when you rebuild with a higher version number

### Uninstalling

```powershell
Get-AppxPackage PressReadyTeam.PressReady | Remove-AppxPackage
```

Or just right-click the app in the Start Menu → Uninstall.

### Portable ZIP

Extract `PressReady_2.0.0-windows-x64.zip` to any folder and run `PressReady.exe`. No installation required. Works from USB drives, network shares, or local folders.

---

## Design Decisions

1. **Separation of concerns**: Engine knows nothing about UI. Data model is shared.
   UI reads/writes data model, engine operates on it.
2. **Vector placement**: All imposition uses `show_pdf_page` — zero rasterization.
   Output PDFs are identical quality to input.
3. **Preview pipeline**: Source preview renders from original PDF. Sheet preview
   creates a temporary imposed PDF and renders it. Both run in background QThreads.
4. **Preprocessor pipeline**: Preprocessors create a temporary modified PDF that
   feeds into the imposition engine. This keeps the pipeline clean and composable.
