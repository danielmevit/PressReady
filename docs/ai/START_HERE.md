# START HERE — PressReady

## What this is
PressReady v2 — a Windows desktop app for **PDF imposition** (laying out source pages on
press sheets for commercial printing). Python 3.10+, PyQt6 UI, PyMuPDF (fitz) engine.
v2.0.0 shipped 2026-02-19 (MSIX + portable ZIP). License: AGPL-3.0-only.

## Current priority
**`ROADMAP.md` — start at Phase 1 (Ground truth).** The plan is grounded in a study of
Imposition Wizard 3 and Toolcraft (`docs/ai/REFERENCE_STUDY.md`); read the roadmap's
one-paragraph summary before touching engine code — it explains why the test harness comes
before every other improvement.

The short version of what's wrong: nothing verifies the output, the UI promises features the
engine ignores (booklet modes, creep, signatures, 9 of 12 preprocessors), and imposition uses
the source MediaBox rather than its TrimBox. See `GOTCHAS.md` before trusting `data_model.py`
as a spec — `engine/impose.py` is the truth.

## How to run
- **App (Windows Python, not WSL):** `pip install PyQt6 PyMuPDF` then `python -m pressready`
- **Engine tests (WSL or Windows):** `pip install -e .[dev]` then `pytest`
- **Installer build (Windows PowerShell):** `powershell -ExecutionPolicy Bypass -File build_msix.ps1`

## Layout of the work
- `pressready/engine/` — data model, imposition, marks, preprocessors. **No Qt imports.**
- `pressready/ui/` — main window, four settings tabs, preview canvas.
- Everything else structural: ask CodeGraph (`codegraph explore "..."`), don't crawl.

## Links
- The plan → `ROADMAP.md` · Recent work → `CHANGELOG.md`
- Why it's built this way → `docs/ai/DECISIONS.md`
- What the references taught us → `docs/ai/REFERENCE_STUDY.md`
- Traps → `docs/ai/GOTCHAS.md` · Theme/styling → `docs/ai/DESIGN_SYSTEM.md`
