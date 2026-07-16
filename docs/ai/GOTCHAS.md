# Gotchas — traps that cost time

## Environment (WSL on /mnt/d)
- **CodeGraph does not auto-sync here** — run `codegraph sync` after editing code.
- **Git push needs Windows credentials:** `cmd.exe /c "git push origin dev"`.
- `core.filemode false` is set — don't "fix" phantom mode diffs.
- `git status` can take minutes: large untracked trees (`pressready-voice/venv`,
  `framer-demo/node_modules`, `dist/`, `build/`) on a slow /mnt mount. Prefer
  `git status -- <path>` or `git ls-files` when possible.
- **Showing the GUI needs Windows Python**, but it can be *constructed* headless in WSL:
  `QT_QPA_PLATFORM=offscreen python -m laydown --smoke` builds the real MainWindow and
  drives a load. The Windows-only calls (`ctypes.windll`, `os.startfile`) live in
  `run_gui()`/menu actions, not at import, so UI logic is testable from WSL.
- **Test venv (WSL):** `~/.venvs/laydown` (PyMuPDF + PyQt6 + pytest). D: has no room for
  it, so it lives on the WSL disk: `~/.venvs/laydown/bin/python -m pytest`.

## PyMuPDF facts worth not re-deriving
- **Box getters/setters use PyMuPDF's top-left origin**, the same space as `page.rect` —
  `page.trimbox = Rect(10, 50, …)` writes a y-flipped `/TrimBox` into the file. So
  `clip=page.trimbox` can be passed straight to `show_pdf_page` without converting.
- **`page.rect` is the CropBox, not the MediaBox** — they differ on trimmed PDFs.
- **Output is not byte-reproducible**: MuPDF randomises the trailer `/ID` per save. Page
  content streams *are* byte-identical, which is what `tests/test_determinism.py` asserts.
- **PDF has no in-place content transform** — scaling artwork means re-placing the page into
  a resized one with `show_pdf_page` (what `_scale` does), which returns a *new* document.

## Known code traps
- **Adding a field to the data model fails the build until you classify it** in
  `engine/capabilities.py` as HONOURED or NOT_IMPLEMENTED. That is deliberate: it is the
  guard against 0.2.0's defect, where the UI collected settings the engine ignored.
  If a setting isn't implemented yet, put it in NOT_IMPLEMENTED — the UI is then
  forbidden from offering it, and `tests/test_capabilities.py` enforces both directions.
- **`ui/schema.py` is the only place settings UI is declared.** Don't hand-build a
  control; add a schema entry. Its `target` is a dotted path into `Project`.
- **Display units are not a schema target** and never reach the engine. The model is
  millimetres throughout; `ValueStore.unit` + `LengthSpin` convert at the widget only.
- **`get_drawings()` ignores clipping**, and reports source paths at their *unclipped*
  extent transformed into sheet space. To check what actually reaches paper, render a
  pixmap and sample it (see `tests/test_source_boxes.py::TestBleed`).
- **`show_pdf_page(rotate=90)` turns anticlockwise** in sheet terms — a source's top edge
  ends up down the sheet's left. Verified against output, not assumed; bleed margins have
  to rotate with it (`geometry.place_page`).
- **`preprocessors.apply_preprocessors` may return a *different* document** (scaling has
  to rebuild pages). The caller owns the input; if the returned doc differs, close both.

## Build / packaging
- **There is no 32-bit Windows build and there cannot be a sensible one.** PyQt6 publishes
  `win_amd64` and `win_arm64` wheels only — no `win32`. Point a 32-bit Python at it and pip
  falls back to `pyqt6-*.tar.gz` and tries to build Qt with qmake, which fails. Shipping x86
  would mean compiling Qt from source for x86. This was attempted in the v0.3.0 release build;
  don't attempt it again. (PyMuPDF *does* ship win32, so it is PyQt6 alone that decides this.)
  Note PyQt6 *does* ship `win_arm64` — a Windows-on-ARM build is possible if ever wanted.
- **Keep `.ps1` files pure ASCII.** Windows PowerShell 5.1 reads a BOM-less `.ps1` as ANSI
  (cp1252), so a UTF-8 em-dash becomes three bytes ending in a curly quote — which PowerShell
  honours as a string terminator. One em-dash in a `Write-Host` message unbalanced every brace
  after it and the script failed to parse before running a line. `tests/test_packaging.py`
  enforces ASCII; it runs on Linux, so a Windows-only trap is caught everywhere.
- **Hosted runner labels get retired, and a retired label queues forever.** The macOS Intel
  job asked for `macos-13`, which GitHub has removed entirely. A job requesting a nonexistent
  label is not rejected — it sits "queued" indefinitely, which blocks the all-platforms release
  gate, and nothing tells you why. If a job queues for more than ~10 minutes while its siblings
  run, check the label against https://github.com/actions/runner-images before anything else.
  Current labels here: `macos-15` (Apple silicon), `macos-15-intel` (Intel).
- **PyInstaller cannot cross-compile.** Every artifact is built on its own OS by
  `.github/workflows/release.yml`. You cannot produce the macOS or 32-bit Windows build
  from this machine; tag a version (or run the workflow by hand) and let CI do it.
- **Never name a build file a case-variant of another.** `packaging/linux/build.sh` used to
  write a launcher called `laydown` beside the `Laydown` binary. On `/mnt/d`
  (case-insensitive) that is the *same file*: the script overwrote the binary and then
  exec'd itself forever. CI's ext4 is case-sensitive, so it would never have caught it. The
  build now hard-fails if the output binary is under 1 MB.
- MSIX build needs a Windows 10 SDK; `certs/` (signing keys) is gitignored. **CI must sign every
  release with the same certificate**: the stable PFX lives in the repo secrets
  `LAYDOWN_CERT_PFX_B64` / `LAYDOWN_CERT_PASSWORD` (created 2026-07-16, CN=LaydownTeam,
  thumbprint 2D87584C..., expires 2031; private copy in local `certs/Laydown.pfx` +
  `laydown-pfx-password.txt`). The certificate subject must equal the manifest Publisher, so
  the rename forced a new cert — the old PressReady one (44ED60F6...) signs nothing anymore.
  Without the secret, `build.ps1` mints a per-run throwaway — that's how the first 0.3.0 MSIX
  shipped signed by a cert that died with the runner, giving every installer 0x800B010A. Users trust
  `Laydown-msix-signing.cer` (attached to each release) once, into LocalMachine\TrustedPeople.
- MSIX needs a **four-part** version and refuses to install over a newer one. `__version__`
  is three parts and the script appends `.0`.
- **The app was PressReady until 0.3.0** (renamed — Fujifilm ships "Revoria XMF PressReady" in
  the same industry). To Windows, `PressReadyTeam.PressReady` and `LaydownTeam.Laydown` are
  unrelated apps: old installs (February's v2.0.0-numbered MSIX *and* 0.3.0) don't upgrade,
  they linger. Remove them with `Get-AppxPackage PressReadyTeam.PressReady | Remove-AppxPackage`
  — keep that OLD identity string; it is not a stale name to "fix". The old PressReady cert
  trust does not cover Laydown's cert either.
- PyInstaller frozen mode resolves icons via `sys._MEIPASS` (`app_icon()` in
  `ui/main_window.py`) — test icon changes in a frozen build, not just from source.
- The site lives in `site/` (Astro) and deploys **from `main`**, not `dev`.

## Qt traps
- **The dark theme needs the palette, not just the stylesheet.** Any widget a QSS rule
  doesn't reach falls back to the platform palette, which is light. `QScrollArea`'s viewport
  is a separate child widget, so `QScrollArea { background: transparent }` misses it — that
  is how the settings panel ended up painting near-white behind near-white titles. Always go
  through `theme.apply(app)`.
- **Widgets don't follow the store on their own.** After undo/redo or a preset load, call
  `SchemaTab.sync_from_store()` — and if you add a control type to `ui/panel.py`, teach
  `sync_from_store` about it. A test enforces that every control is resyncable.
- Watch for local names shadowing `theme as t` (`for t in ...` cost an hour).

## Repo oddities
- `pressready-voice/` (tray dictation app) and `framer-demo/` (web demo) are **separate
  side-projects** living in this folder; both are excluded from CodeGraph via
  `codegraph.json`. `_legacy/` on disk is untracked leftover (already deleted from git).
