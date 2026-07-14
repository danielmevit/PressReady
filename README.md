# PressReady v2

**PressReady** is a Windows desktop app for **PDF imposition** — laying out source pages on press sheets for commercial printing. Version 2 is written in **Python 3.10+** with **PyQt6** and **PyMuPDF (fitz)**. 

---

## Installers

| Format | File | Notes |
|--------|------|--------|
| **MSIX** | `PressReady_2.0.0.msix` | Standard install: Start Menu, Settings → Apps, uninstall from the system. |
| **Portable ZIP** | `PressReady_2.0.0-windows-x64.zip` | Run `PressReady.exe` after extract; no install. Handy for USB or locked-down machines. |

Built by `build_msix.ps1` into `installer_output/`.

---

## Interface

Work is grouped into four tabs:

| Tab | Role |
|-----|------|
| **Source** | Which box of the incoming pages to impose (trim/bleed/crop/media), bleed, and page transforms. |
| **Layout** | N-Up grids, booklets (saddle stitch or perfect bound), signatures, creep, gutters, page range. |
| **Sheet** | Press sheet size (A5–A2, Letter, Legal, Tabloid, custom), margins, orientation. |
| **Marks** | Crop, gap crop, trim, registration, folding, perforation, collating, colour bar, labels, custom PDF marks. |

The settings panel is generated from a single declarative schema (`pressready/ui/schema.py`),
and a control cannot exist unless the engine honours the setting behind it — the test suite
fails otherwise. Settings that don't apply to the current mode are hidden rather than greyed
out.

---

## What works today

- **Box-aware imposition** — imposes the **trim box** by default, so a press-ready PDF places
  its finished page, not its whole sheet. Bleed carries artwork past the cut line. Files with
  no boxes are unaffected.
- **Vector throughout** — pages are embedded via `show_pdf_page`, never rasterized, so output
  quality always equals the source.
- **Layout** — N-Up at 1/2/4/6/8/9/16-up or any rows × columns, auto-rotate to fit, booklets
  (saddle stitch or perfect bound with signatures), creep compensation, right-to-left binding,
  gutters, page ranges.
- **Source transforms** — rotate, scale (a true photographic scale, boxes and all), reorder.
- **Marks** — crop, gap crop, trim, registration, folding, perforation, collating, colour bar,
  text labels, and **custom marks: any PDF stamped on the sheet** (bring your own bull's-eye).
- **Preflight** — impossible margins, a missing trim box, bleed with no artwork behind it,
  mixed page sizes, page counts that don't fold, unwanted scaling — reported while you can
  still fix them, not at the press.
- **Preview is the output** — sheets are rendered from a real imposition, and the magenta cut
  lines come from that same run, so they cannot disagree with what prints.
- **Units** — mm, cm, inches or points.
- Undo/redo, per-section reset, presets (readable JSON), recent files, drag-and-drop,
  background export with a working Cancel, in-app help (F1), preflight (F7).

Details: [CHANGELOG.md](CHANGELOG.md).

## License

**GNU Affero General Public License v3.0 (AGPL-3.0-only).** See [`LICENSE`](LICENSE), [`LICENSING.md`](LICENSING.md), and [`NOTICE`](NOTICE).

**No warranty — use at your own risk.** The software is provided **“as is”** without warranty. You are responsible for verifying output (imposed PDFs, print readiness) before production use. The full disclaimer of warranty and limitation of liability is in [`LICENSE`](LICENSE) (AGPL sections 15–17). This README is not legal advice.

### Roadmap

See [ROADMAP.md](ROADMAP.md). Next up: more preprocessors (clone, split, N+1, center/crop),
step-and-repeat and cut-stack layouts, a CLI for batch work, and work-and-turn/tumble press
forms (deliberately not guessed at — see the roadmap for why).

---

## Repository layout

```
PressReady/
├── pressready/
│   ├── __main__.py          # Entry point (--smoke, --version)
│   ├── engine/              # Qt-free: model, geometry, impose, marks,
│   │                        # preprocessors, preflight, capabilities
│   └── ui/                  # schema, panel, components, theme, preview
├── assets/icons/
├── tests/                   # 230 tests, incl. a ground-truth bench harness
├── docs/ai/                 # How to work in this repo (start: AGENTS.md)
├── PressReady.spec
├── AppxManifest.xml
├── build_msix.ps1
├── pyproject.toml
├── CHANGELOG.md
├── LICENSE                  # GNU AGPL v3.0
├── LICENSING.md
├── NOTICE
├── installer_output/        # Build output (not in git)
└── README.md
```

---

## Run from source

```bash
cd PressReady
pip install PyQt6 PyMuPDF
python -m pressready

python -m pressready --smoke   # headless end-to-end self-check, exits 0/1
```

Tests (the engine is Qt-free, so they run headless anywhere):

```bash
pip install -e ".[dev]"
pytest
```

---

## Build MSIX (Windows)

Uses **PyInstaller** and the **Windows SDK** (`makeappx`, `signtool`).

**Requirements:** Python 3.10+ with PyQt6 and PyMuPDF, PyInstaller, and a Windows 10 SDK (example: `winget install Microsoft.WindowsSDK.10.0.26100`).

```powershell
powershell -ExecutionPolicy Bypass -File build_msix.ps1
```

This bundles the app, creates or reuses a cert under `certs/`, builds a signed `installer_output/PressReady_2.0.0.msix`, and a portable zip. Use `-SkipPyInstaller` if `dist/PressReady/` is already up to date.

**Trust the signing certificate once (elevated PowerShell):**

```powershell
Import-Certificate -FilePath "certs\PressReady.cer" -CertStoreLocation Cert:\LocalMachine\TrustedPeople
```

**Install / remove:**

```powershell
Add-AppxPackage -Path installer_output\PressReady_2.0.0.msix
Get-AppxPackage PressReadyTeam.PressReady | Remove-AppxPackage
```

Portable build: unzip `PressReady_2.0.0-windows-x64.zip` and run `PressReady.exe`.

---

## Design notes

1. **Engine vs UI** — The engine imports no Qt; a shared dataclass model is the contract. That
   is what makes the whole engine testable headless, and would let a CLI reuse it.
2. **Vectors** — Imposition uses `show_pdf_page`, so quality follows the source PDF.
3. **One geometry** — `engine/geometry.py` decides what goes where; `impose.py` only renders
   that plan, and the preview annotates the result the engine hands back. There is no second
   opinion about layout anywhere in the codebase.
4. **The UI cannot promise what the engine ignores** — every setting is classified in
   `engine/capabilities.py`, and adding one to the model fails the build until it is. This is
   deliberate: v2.0.0 shipped a Layout tab whose booklet modes, signatures and creep the engine
   silently discarded.
5. **Millimetres in the model** — units are a display concern only, converted at the widget.
