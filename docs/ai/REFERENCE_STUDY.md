# Reference study — Imposition Wizard 3 and Toolcraft

Grounding for `ROADMAP.md` (per `_refs/ai-full-build-recipe.md` §1: plan from the reference,
not from imagination). Two references, two different jobs:

| Reference | Studied for | Studied how |
|-----------|-------------|-------------|
| **Imposition Wizard 3** (Appsforlife) | The *feature and domain model* of a mature imposition tool | Its install folder: `C:\Program Files\Appsforlife\Imposition Wizard 3` — shipped files + printable strings in `ImpositionWizard.exe` |
| **Toolcraft** (`npx @pixel-point/toolcraft create`) | The *UI architecture and design language* | The published npm package's templates + `docs/toolcraft/` rules |

**No code from either was copied.** IW is a proprietary Qt5/QML app; what's recorded below is
its observable feature surface and architecture. Toolcraft is a React/Tailwind web stack —
PressReady is PyQt6, so nothing is portable by copy anyway; only the *ideas* transfer.

---

## 1. Imposition Wizard 3 — what a mature imposition tool has

**Stack:** Qt5 Quick/QML (`Qt5Quick.dll`, `QtQuickControls2`, `QtGraphicalEffects`), a custom
QML control kit (`Button`, `ComboBox`, `NumericField`, `Slider`, `Title`) with a **`Theme.qml`
singleton** holding the tokens. Entry: `qrc:/qml/MainWindow.qml`.

**Its four tabs are PressReady's four tabs.** Verbatim from the binary:
```
readonly property variant tabs: ["InputPanel", "LayoutPanel", "SheetPanel", "MarksPanel"]
```
PressReady v2's Preprocessors / Layout / Sheet / Marks is a direct lift of that structure, and
its `data_model.py` enums are IW's feature list transcribed — which is why so many are
unimplemented (see `GOTCHAS.md`). **IW is the source of the promises PressReady's UI makes.**

| Area | IW ships | PressReady today |
|------|----------|------------------|
| **Layout modes** | N-Up, Booklet, **Cut Stack**, **Dutch Cut**, **Step and Repeat**, Shuffle | N-Up (2/4 only), Booklet (saddle-stitch only) |
| **N-Up grid** | Arbitrary `Rows` × `Columns` | Hardcoded 2×1 / 2×2 |
| **Booklet** | Creep (`CreepCalculatorMode`, `CreepCalculatorScale`), signatures | Model declares them; engine ignores them |
| **Input/preprocess** | Clone, N+1, Split, Shuffle, Resize (by Width/Height/Percentage/Size), Override Box, Bleeds Override, Center and Crop, Slice | 3 of 12 declared (rotate, scale, reorder) |
| **Marks** | Crop, **Gap Crop**, Folding, Collating, **Perforation**, **Angle**, **Custom** | Crop, Trim, Registration, Folding, Text, Collating |
| **Mark assets** | `Placeholders/`: `missing-bull-eye.pdf`, `missing-color-bar.pdf`, `missing-custom-mark.pdf`, `missing-star-target.pdf` | — |
| **Barcodes** | Full `BarcodesLib`: Code128/39/93, EAN8/13, DataMatrix, Aztec, GS1, DataBar, ISBN13, Codabar… | — |
| **Boxes** | MediaBox/BleedBox/TrimBox aware (`bleedBoxSize`, `Bleeds Override`) | **Ignored** — always the MediaBox |
| **Units** | millimeters, centimeters, inches, points | mm only |
| **Preflight** | `PreflightDashboard`, `PreflightIndicator`, `PreflightOnImposition` | — |
| **Presets** | `PresetsPopup`, `PagePresets` | Settings dialog is a "future update" stub |
| **Automation** | `Batch.qml`, `HotFolders.qml`, `iwc.exe` (console binary, ships beside the GUI) | — |
| **Integration** | `ImpositionWizardPlugin64.api` — an **Adobe Acrobat plugin** of the same engine | — |
| **Misc** | Localized (incl. Polish), OpenGL/Graphics settings page, update checker, licensing | — |

### The two architecture insights worth stealing
1. **A "custom mark" is just a PDF stamped onto the sheet.** The `Placeholders/*.pdf` files are
   the fallbacks shown when a user's mark PDF is missing — so color bars, star targets and
   bull's-eyes are *user-supplied PDF assets placed by rule*, not drawing code. PressReady gets
   this nearly free: `show_pdf_page` already does exactly that placement.
2. **One engine, three front-ends** (GUI, `iwc` console, Acrobat plugin). Only possible because
   the engine is UI-free — the same reason PressReady's engine bans Qt imports
   (`DECISIONS.md`). It validates the CLI/batch direction.

### What NOT to take from IW
- **Shuffle** — IW's own UI calls it deprecated (`Shuffle jest przestarzały`).
- **30+ barcode symbologies** — huge scope, thin value. One or two (Code128, DataMatrix) if ever.
- **Licensing/subscription/registration machinery** — PressReady is AGPL-3.0.
- **Its visual style** — that's Toolcraft's job below. IW is studied for *what*, not *how it looks*.

---

## 2. Toolcraft — the UI architecture and design language

Package: `@pixel-point/toolcraft@0.0.14`. Ships a starter app + a UI kit + `docs/toolcraft/`
rules. The visual polish is downstream of one structural idea:

### The idea: the control panel is declared, not hand-wired
`src/app/app-schema.ts` is *the public product surface*. `defineToolcraft` declares
`panels.controls.sections` → controls, each with `type`, `target`, `defaultValue`, `label`,
`description`, `visibleWhen`. The runtime renders the panel, owns state, reset, undo/redo,
persistence, and settings import/export. Nothing is hand-built per app.

Consequences that matter to PressReady:
- **`visibleWhen`, never `disabled`.** Their rule, verbatim: *"Use `visibleWhen` for inactive
  product branches so the panel shows only usable controls. Do not use `disabled: true` or
  `disabledWhen` for generated product controls."* A section with no visible controls hides
  itself. **This is precisely PressReady's biggest defect stated as a design law** — a control
  that can't do anything must not be on screen.
- **Structure becomes testable.** `starterControlSectionInventory` (every control target appears
  exactly once, with the entity it edits and why it's grouped) plus `orderRole` make panel
  structure assertable in tests, not review-by-eye.
- **Reset/undo/presets are free** once values live in one declared store.

### Their layout laws (the density that reads as "polish")
- Sections come from **product entities/workflow stages, not component types**. 2–7 controls each.
  Titles name the edited thing (`Background`, `Motion`, `Export`) — **never** `Settings`,
  `Options`, `Controls`, `Colors`.
- Every section: standard **36px collapsible header** with a per-section reset that restores only
  that section's targets to `defaultValue`. 8px top / 24px bottom content spacing.
- Labels short; **no `Enable` prefix on switches** (the switch already says on/off); drop nouns the
  section title supplies (`Include`, not `Include background`); help icon only when the
  description adds meaning beyond the label.
- Sliders and segmented controls are **full-width, never in a row**. Segmented only for ≤4 options,
  ≤9 chars each. Inline 50/50 rows only for short related pairs; stack if anything clips.
- **Final delivery actions live in a sticky footer** (`panelActions`), not in the body or canvas.
- Compound controls are **atomic** — `colorOpacity` owns colour+opacity; never split an owned field
  into neighbouring controls.

### The visual tokens
Dark-first, `oklch` palette, Inter Variable, `--accent: #0c8ce9`, `--muted: #262626`; radius scale
2/4/6/8/12px; **4px scrollbars**, 999px thumbs at `color-mix(foreground 10%)`, min thumb 2.75rem;
focus rings only under `[data-focus-visible-mode="keyboard"]`; animations suppressed while controls
mount (`[data-toolcraft-controls-mounting]`) so panels don't flash.

**Port note:** Qt stylesheets have no `oklch()` or `color-mix()`. The palette must be computed to
hex in Python (`ui/theme.py`) and the tokens emitted into QSS — same values, different pipe.
