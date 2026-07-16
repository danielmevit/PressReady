# Decisions — durable "why" choices

- **Python + PyQt6 + PyMuPDF for v2** (over the v1 codebase). v1 is archived; the repo's
  history has it under `_legacy/v1` (later removed from git; a copy may linger on disk).
- **Vector imposition via `show_pdf_page`** — pages are embedded as XObjects, never
  rasterized, so output quality always equals source quality. This is the core product
  promise; nothing in the pipeline may rasterize page content.
- **Engine/UI split with a shared dataclass model** (`laydown/engine/data_model.py`).
  The engine imports no Qt. UI tabs each expose a `get_*()` that assembles the `Project`.
  Rationale: headless testability + the engine could later back a CLI/batch mode.
- **Preview = render the real imposed PDF** — the preview canvas imposes to a temp PDF and
  rasterizes that, so the preview is the actual output, not a simulation. (Caveat: overlay
  cell geometry is computed separately — see GOTCHAS.)
- **MSIX + portable ZIP, no third-party installer** — packaging uses only the free Windows
  10 SDK (`makeappx`, `signtool`) via `build_msix.ps1`. Inno Setup was removed.
- **AGPL-3.0-only** license (relicensed after 0.2.0; see LICENSING.md).
- **mm in the model, points in the engine** — all user-facing/model dimensions are mm;
  conversion to PDF points happens at the engine boundary (`utils.mm_to_pt`).

## 2026-07-14 — after the Imposition Wizard / Toolcraft reference study

- **Keep PyQt6 + PyMuPDF; port Toolcraft's design language, don't adopt its stack.** Toolcraft is
  React/Vite/Tailwind. Laydown's value is the PyMuPDF vector engine and MSIX desktop packaging;
  a web rewrite would discard a shipped 0.2.0 to gain styling. What transfers is the *schema-driven
  panel* idea and the visual system, recreated in Qt (`ROADMAP.md` Phases 3–4).
- **A control that the engine doesn't honour must not exist in the UI** — Toolcraft's
  `visibleWhen`-never-`disabled` law. Enforced by an engine capability registry plus a test, not by
  discipline (Phase 3). This is the direct answer to the v2 defect where the Layout tab collected
  creep/signatures/booklet modes that `impose.py` ignored.
- **Imposition Wizard is a domain reference, not a feature target.** Its enum surface is what
  Laydown's UI transcribed and then failed to implement. Take its domain model and its
  one-engine-many-front-ends architecture; skip Shuffle (deprecated in IW itself), the 30+ barcode
  symbologies, and the licensing machinery. See `REFERENCE_STUDY.md`.
- **Brand accent stays orange (`#D07B24`)** rather than Toolcraft's blue — it's already in the app
  icon and MSIX tiles. "Similar to Toolcraft" means its neutrals, density and control anatomy, not
  its identity.
- **Evaluation before features** — the bench harness lands before any change to imposition output
  (recipe §5). `tests/` was empty through 0.2.0; every layout improvement after this is measured.

## 2026-07-16 — the rename

- **PressReady → Laydown at 0.4.0.** Fujifilm ships "Revoria XMF PressReady" — a prepress
  workflow product that pre-flights, *imposes* and gangs jobs, i.e. the same field. "Laydown"
  is genuine pressroom vocabulary for the imposition arrangement itself, and searches found no
  software using it (GitHub and PyPI names were free; "Impoze", "Octavo" — a direct competitor
  imposition app — "Sheetwise" and "Perfector" were all taken). Chosen by Daniel over Frisket
  and Foldo.
- Consequences accepted knowingly: new MSIX identity (`LaydownTeam.Laydown`) and a **new
  signing certificate** (subject must match Publisher), so old PressReady installs don't
  upgrade and the old cert trust doesn't carry over; the GitHub Pages URL moved (no redirect);
  repo URL redirects via GitHub. Old releases keep their PressReady artifact names — renaming
  published binaries would lie about what they are.
