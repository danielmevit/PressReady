# ProjectContext.md

## Changelog (most recent first)
> Curated summary only. Detailed history lives in git commits.

- 2026-01-29 21:30 Europe/Prague (UTC+01:00) - Build/Version: v0.6.0
  - Stage 5 complete: Crop marks, registration marks, page labels implemented
  - Custom sheet sizes added (50-1000mm range)
  - Page labels repositioned 10% inward to avoid crop mark overlap

## Project overview
- **Product**: PressReady (standalone PDF imposition app)
- **Platforms**: Windows (tested), macOS/Linux (untested, should work)
- **Tech**: Python 3.10+, PyQt6, PyMuPDF (fitz)
- **Core principles**:
  - Export is vector stamping (`show_pdf_page`) - no rasterization
  - Preview is image rendering for verification only
  - Engine and UI are separated (modular design)
  - Imposition-focused - not a general PDF viewer

## Stage completion (evidence-based)

### Stage 0 (setup/tests/samples): DONE
- **Evidence**:
  - `pyproject.toml` - dependencies defined (PyQt6, PyMuPDF, pytest)
  - `pressready/__main__.py` - entry point exists
  - `tests/test_utils.py` - 22 tests for `mm_to_pt`, `pt_to_mm`, `parse_page_range`
  - `samples/.gitkeep` - samples folder exists
- **Verify**: `python -m pressready` opens window; `pytest tests/test_utils.py` passes
- **Gaps**: None

### Stage 1 (N-Up engine): DONE
- **Evidence**:
  - `pressready/engine/impose.py` lines 223-396: `impose_nup()` function
  - `pressready/engine/utils.py` lines 12-113: `mm_to_pt()`, `parse_page_range()`
  - `tests/test_impose.py` lines 66-331: 12 tests for N-Up
  - `pressready/tools/impose_nup_demo.py` - demo script
- **Verify**: `python -m pressready.tools.impose_nup_demo input.pdf output.pdf`
- **Gaps**: None

### Stage 2 (UI previews): DONE
- **Evidence**:
  - `pressready/ui/main_window.py` lines 248-284: `PreviewLabel` class
  - `pressready/ui/main_window.py` lines 112-245: `PreviewWorker` class
  - `pressready/ui/main_window.py` lines 496-560: source preview panel with navigation
  - `pressready/ui/main_window.py` lines 317-321: debounce timer (200ms)
  - Drag-drop: `setAcceptDrops(True)` at line 331
- **Verify**: Load PDF, use prev/next buttons, change settings → preview updates
- **Gaps**: None

### Stage 3 (Export): DONE
- **Evidence**:
  - `pressready/ui/main_window.py` lines 43-110: `ExportWorker` class with progress signal
  - `pressready/ui/main_window.py` lines 324-328: worker connections
  - `pressready/engine/impose.py` lines 236, 332-334, 387-389: `progress_callback` parameter
- **Verify**: Export button → progress dialog → success message
- **Gaps**: None

### Stage 4 (Booklet): DONE
- **Evidence**:
  - `pressready/engine/impose.py` lines 399-437: `calculate_booklet_page_order()`
  - `pressready/engine/impose.py` lines 440-610: `impose_booklet()`
  - `tests/test_impose.py` lines 334-432: booklet tests
  - UI: `_layout_combo` has "Booklet" option (line 408)
- **Verify**: Select "Booklet" layout, export → produces saddle-stitch ordered PDF
- **Gaps**: None

### Stage 5 (Marks + bleed warnings): DONE
- **Evidence**:
  - `pressready/engine/impose.py` lines 38-56: `draw_registration_mark()`
  - `pressready/engine/impose.py` lines 59-111: `draw_page_labels()`
  - `pressready/engine/impose.py` lines 114-154: `draw_registration_marks_on_sheet()`
  - `pressready/engine/impose.py` lines 157-191: `draw_crop_marks()`
  - UI checkboxes: lines 470-482
  - `tests/test_impose.py` lines 435-509: crop marks tests
- **Verify**: Enable checkboxes, set margin ≥10mm, export → marks visible in output
- **Gaps**: 
  - Bleed warnings: NOT implemented (no visual warning for insufficient bleed)
  - Color bars: NOT implemented

## What's implemented (behavior summary)

### UI capabilities
- Load PDF via button or drag-drop
- Source preview with prev/next navigation and slider
- Sheet preview with prev/next navigation and slider
- Real-time preview updates with 200ms debounce
- Export with progress dialog and success/error messages
- Settings: layout mode, sheet size, orientation, margin, gap, page range
- Marks: crop marks, registration marks, page labels (all optional)
- Custom sheet sizes (50-1000mm)

### Layouts supported
- **2-Up**: 2 pages per sheet (2×1 grid)
- **4-Up**: 4 pages per sheet (2×2 grid)
- **Booklet**: Saddle-stitch with auto-padding to multiple of 4

### Preview behavior
- Source: renders single page at 120 DPI
- Sheet: generates temp imposed PDF, renders selected sheet at 120 DPI
- Both use background workers (no UI freeze)

### Export behavior
- Background worker with progress callback
- Vector placement via `show_pdf_page` (no rasterization)
- Output filename suggests: `{base}_{layout}_{sheetsize}{marks}.pdf`
- Marks suffixes: `_cm` (crop marks), `_reg` (registration marks)

### Known limitations
- No creep adjustment for booklets
- No auto-rotate for mixed orientation pages
- No bleed support (Trim/Bleed box handling)
- No presets save/load
- Registration marks require ≥10mm margin
- Page labels require ≥8mm margin

## Repo map (key folders)
- `pressready/engine/` - Imposition logic, pure Python, no UI dependencies
- `pressready/ui/` - PyQt6 main window and preview components
- `pressready/tools/` - CLI utilities (pdf_info, impose_nup_demo, generate_sample_pdf)
- `tests/` - pytest tests for engine modules
- `samples/` - Sample PDFs for testing (mostly empty, generated on demand)

## Key files & responsibilities
- `pressready/__main__.py` - Entry point, creates QApplication and MainWindow
- `pressready/version.py` - Single source of truth for version
- `pressready/engine/utils.py` - `mm_to_pt()`, `pt_to_mm()`, `parse_page_range()`
- `pressready/engine/impose.py` - `impose_nup()`, `impose_booklet()`, mark drawing functions
- `pressready/ui/main_window.py` - MainWindow, PreviewWorker, ExportWorker, PreviewLabel
- `tests/test_utils.py` - Unit conversion and page range tests
- `tests/test_impose.py` - N-Up, Booklet, and crop marks integration tests

## How to run
```bash
cd "D:\Vibe Coding\PressReady"
python -m pressready
```

## How to test
```bash
cd "D:\Vibe Coding\PressReady"
pytest                           # All tests
pytest tests/test_utils.py       # Utils only
pytest tests/test_impose.py      # Imposition only
pytest -v                        # Verbose output
```

**What tests cover**:
- Unit conversion accuracy (mm ↔ pt)
- Page range parsing (single, ranges, mixed, errors)
- N-Up sheet count calculations
- N-Up output sheet sizes (A3/A4)
- Booklet page ordering algorithm
- Crop marks presence in output
- Vector placement verification (XObject check)

## PDF box strategy
- **Trim precedence**: Not implemented - uses MediaBox only
- **Bleed usage**: Not implemented
- **Fallbacks**: Source page rect used as-is

## Mixed pages, scaling, rotation strategy
- **Mixed sizes**: Pages scaled to fit cell with `keep_proportion=True`
- **Scaling**: Proportional fit to cell rectangle
- **Rotation**: Not handled - pages placed as-is

## Duplex/flip conventions (booklets)
- **Current meaning of "front/back"**: 
  - Sheet N Front = output page (N-1)*2
  - Sheet N Back = output page (N-1)*2 + 1
- **Future intent**: Document flip-on-long-edge vs flip-on-short-edge

## Presets
- **Status**: NOT IMPLEMENTED
- **Format**: N/A
- **preset_schema_version**: N/A
- **Migration plan**: N/A

## Logging & error policy
- **Warnings vs errors**: Qt font warnings suppressed, ValueError for invalid inputs
- **Where logs appear**: Terminal stdout, Qt message boxes for export errors

## Performance targets
- **Preview DPI default**: 120 (balance of quality/speed)
- **Preview update target**: 200ms debounce
- **Export expectations**: Fast (PyMuPDF vector ops), tested up to 500 pages
- **Caching summary**: None currently (temp files deleted after use)

## Output naming & metadata (slugs)
- **Current**: `{basename}_{layout}_{sheet}{marks}.pdf`
  - Layout: `2up`, `4up`, `booklet`
  - Sheet: `A3`, `A4`, `300x450mm` (custom)
  - Marks: `_cm`, `_reg`
- **Planned**: Include page range, timestamp, source metadata

## Known issues / risks
- Windows temp file permissions can cause test failures in sandboxed environments
- Qt font warnings on Windows (suppressed but harmless)
- Large PDFs (1000+ pages) may cause memory pressure on 32-bit systems
- No input validation for corrupt PDFs (PyMuPDF handles gracefully)

## Next steps (near term, prioritized)
1. **Save/Load Presets** - Acceptance criteria: JSON schema with version, load/save buttons work, migration for old versions
2. **Creep Adjustment** - Acceptance criteria: Slider 0-5mm, inner pages shift outward progressively
3. **Auto-rotate pages** - Acceptance criteria: Detect landscape pages, rotate to match cell orientation

## Quality-of-life roadmap (mid term)
- **Color bars** - CMYK strips in margin for press calibration
- **Bleed support** - Respect TrimBox/BleedBox, extend content to bleed
- **Custom marks** - User-defined mark templates
- **Batch processing** - Process multiple PDFs with same settings
- **Print-ready checks** - Validate resolution, color space, fonts

## Print-grade PRD items (roadmap/notes)
- **Preset schema versioning + migrations**: Define v1 schema, auto-upgrade on load
- **Deterministic regression strategy**: Pin page order + rects in tests, cross-OS verification
- **PDF box strategy**: Priority: TrimBox > CropBox > MediaBox; BleedBox for extension
- **Duplex/flip conventions**: Document front=long-edge-flip assumption
- **Logging + error policy**: Define warning vs error levels, structured logging
- **Performance targets**: <500ms preview, <5s export per 100 pages
- **Output naming policy**: Template-based with variables
- **Mixed page sizes/rotation policy**: Auto-fit vs error vs manual choice

## Release/Packaging notes (basic)
- **PyInstaller**: Bundle with `--onefile --windowed --name PressReady`
- **Dependencies to bundle**: PyQt6, PyMuPDF, standard library
- **Platform notes**: Windows tested, macOS/Linux need testing
- **Installer**: Consider NSIS for Windows installer with Start Menu shortcut

## Persisted info
- Export must remain vector stamping (`show_pdf_page`)
- Previews are verification renders only (image-based)
- Keep scope focused on imposition (not a PDF viewer)
- Engine/UI separation must be maintained
