"""
Placement geometry — the single answer to "what goes where on which sheet".

Both the imposition engine and the preview overlay need this. They used to work it
out separately, which meant the magenta overlay could quietly disagree with the
printed result; everything now plans through :func:`sheet_plan`.

Two rects matter for every placed page and they are not the same:

* **place box** — the box that is fitted to the cell. Normally the TrimBox: the
  finished, cut page. This is what crop marks must mark.
* **clip box** — the area actually drawn, which is the place box plus any bleed.
  It deliberately spills outside the cell so a slightly-off cut still hits ink.

All rects are PDF points in PyMuPDF's top-left coordinate space.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import fitz

from pressready.engine.data_model import (
    LayoutType,
    Project,
    SourceBox,
    SourceSettings,
)
from pressready.engine.utils import mm_to_pt


# ── sheet-level geometry ─────────────────────────────

def sheet_size_pt(project: Project) -> Tuple[float, float]:
    """(width, height) of the press sheet in points."""
    w_mm, h_mm = project.sheet.sheet_size_mm()
    return mm_to_pt(w_mm), mm_to_pt(h_mm)


def margins_pt(project: Project) -> Tuple[float, float, float, float]:
    """(left, right, top, bottom) margins in points."""
    s = project.sheet
    return (
        mm_to_pt(s.margin_left_mm),
        mm_to_pt(s.margin_right_mm),
        mm_to_pt(s.margin_top_mm),
        mm_to_pt(s.margin_bottom_mm),
    )


def grid_for(layout) -> Tuple[int, int]:
    """(cols, rows) for an N-Up layout."""
    if layout.rows and layout.cols:
        return layout.cols, layout.rows
    nup = layout.nup
    if nup == 2:
        return 2, 1
    if nup == 4:
        return 2, 2
    raise ValueError(f"nup must be 2 or 4 (or set rows/cols explicitly), got {nup}")


def cell_grid(project: Project, cols: int, rows: int) -> List[fitz.Rect]:
    """The cols×rows cells of a sheet, in reading order."""
    sheet_w, sheet_h = sheet_size_pt(project)
    ml, mr, mt, mb = margins_pt(project)
    gh = mm_to_pt(project.layout.gutter_h_mm)
    gv = mm_to_pt(project.layout.gutter_v_mm)

    cell_w = (sheet_w - ml - mr - (cols - 1) * gh) / cols
    cell_h = (sheet_h - mt - mb - (rows - 1) * gv) / rows
    if cell_w <= 0 or cell_h <= 0:
        raise ValueError("Margins/gutters too large for sheet size")

    cells = []
    for i in range(cols * rows):
        col, row = i % cols, i // cols
        x0 = ml + col * (cell_w + gh)
        y0 = mt + row * (cell_h + gv)
        cells.append(fitz.Rect(x0, y0, x0 + cell_w, y0 + cell_h))
    return cells


# ── source boxes ─────────────────────────────────────

def _raw_box(page: fitz.Page, which: SourceBox) -> fitz.Rect:
    if which == SourceBox.MEDIA:
        return page.mediabox
    if which == SourceBox.CROP:
        return page.cropbox
    if which == SourceBox.BLEED:
        return page.bleedbox
    return page.trimbox


def source_boxes(page: fitz.Page, source: SourceSettings) -> Tuple[fitz.Rect, fitz.Rect]:
    """
    Return (place_box, clip_box) for *page*.

    PDF defines TrimBox/BleedBox to default to the CropBox, and PyMuPDF honours that,
    so asking for the TrimBox of a plain PDF that has none simply yields the whole
    page — which is why TrimBox is a safe default rather than a risky one.
    """
    box = _raw_box(page, source.box) & page.rect
    if box.is_empty:
        box = fitz.Rect(page.rect)

    if source.bleed_mm <= 0:
        return box, box

    b = mm_to_pt(source.bleed_mm)
    clip = fitz.Rect(box.x0 - b, box.y0 - b, box.x1 + b, box.y1 + b) & page.rect
    if clip.is_empty:
        return box, box
    return box, clip


# ── fitting a page into a cell ───────────────────────

def fitted_rect(cell: fitz.Rect, width: float, height: float) -> fitz.Rect:
    """Where a width×height box lands inside *cell*, fitted and centred."""
    scale = min(cell.width / width, cell.height / height)
    w, h = width * scale, height * scale
    x0 = cell.x0 + (cell.width - w) / 2
    y0 = cell.y0 + (cell.height - h) / 2
    return fitz.Rect(x0, y0, x0 + w, y0 + h)


def target_rect(cell: fitz.Rect, place: fitz.Rect, clip: fitz.Rect) -> Tuple[fitz.Rect, fitz.Rect]:
    """
    Work out where to draw so that *place* lands exactly on the cell.

    Returns (target, trim) where *target* is the rect to hand ``show_pdf_page``
    (sized for the clip, so bleed spills outside the cell) and *trim* is where the
    place box ends up on the sheet — the rect crop marks must follow.

    A page whose proportions don't match the cell is letterboxed inside it, so trim
    is often smaller than the cell. Marking the cell instead of the trim is how you
    get crop marks that miss the page.
    """
    trim = fitted_rect(cell, place.width, place.height)
    if clip == place:
        return trim, trim

    scale = trim.width / place.width
    target = fitz.Rect(
        trim.x0 - (place.x0 - clip.x0) * scale,
        trim.y0 - (place.y0 - clip.y0) * scale,
        trim.x1 + (clip.x1 - place.x1) * scale,
        trim.y1 + (clip.y1 - place.y1) * scale,
    )
    return target, trim


# ── page ordering ────────────────────────────────────

def booklet_page_order(n: int) -> List[Tuple[int, int]]:
    """
    Saddle-stitch page ordering.

    Returns (left, right) pairs, 0-based, one per printed side; -1 means blank.
    Facing pages always sum to padded-1 — that is what makes a folded signature
    read in order.
    """
    padded = ((n + 3) // 4) * 4
    result = []
    lo, hi = 0, padded - 1
    while lo < hi:
        result.append((hi, lo))
        lo += 1
        hi -= 1
        result.append((lo, hi))
        lo += 1
        hi -= 1
    return [(l if l < n else -1, r if r < n else -1) for l, r in result]


# ── the plan ─────────────────────────────────────────

@dataclass(frozen=True)
class Placement:
    """One source page in one cell of one sheet."""
    cell: fitz.Rect
    page_index: int  # index into the source document; -1 = deliberately blank


@dataclass(frozen=True)
class Sheet:
    """One printed side of the output."""
    placements: List[Placement]
    number: int                      # physical sheet, 1-based
    total: int                       # physical sheets in the job
    side: str = ""                   # "", "Front" or "Back"
    fold_x: Optional[float] = None   # x of the fold line, booklet only

    @property
    def cells(self) -> List[fitz.Rect]:
        return [p.cell for p in self.placements]


def sheet_plan(project: Project, page_indices: List[int]) -> List[Sheet]:
    """
    Plan the whole job: which source page goes in which cell of which sheet.

    The one place layout decisions are made. The imposition engine renders this
    plan; the preview draws its overlays from the same plan, so they cannot drift.
    """
    if project.layout.layout_type == LayoutType.BOOKLET:
        return _plan_booklet(project, page_indices)
    return _plan_nup(project, page_indices)


def _plan_nup(project: Project, page_indices: List[int]) -> List[Sheet]:
    cols, rows = grid_for(project.layout)
    cells = cell_grid(project, cols, rows)
    per_sheet = cols * rows

    n = len(page_indices)
    num_sheets = max(1, (n + per_sheet - 1) // per_sheet)

    sheets = []
    for si in range(num_sheets):
        placements = []
        for ci in range(per_sheet):
            idx = si * per_sheet + ci
            if idx >= n:
                break
            placements.append(Placement(cells[ci], page_indices[idx]))
        sheets.append(Sheet(placements=placements, number=si + 1, total=num_sheets))
    return sheets


def _plan_booklet(project: Project, page_indices: List[int]) -> List[Sheet]:
    cells = cell_grid(project, 2, 1)
    order = booklet_page_order(len(page_indices))
    num_sheets = max(1, len(order) // 2)

    _, _, _, _ = margins_pt(project)
    gh = mm_to_pt(project.layout.gutter_h_mm)
    fold_x = cells[0].x1 + gh / 2 if gh else cells[0].x1

    sheets = []
    for si, (lp, rp) in enumerate(order):
        placements = []
        if lp >= 0:
            placements.append(Placement(cells[0], page_indices[lp]))
        if rp >= 0:
            placements.append(Placement(cells[1], page_indices[rp]))
        sheets.append(Sheet(
            placements=placements,
            number=si // 2 + 1,
            total=num_sheets,
            side="Front" if si % 2 == 0 else "Back",
            fold_x=fold_x,
        ))
    return sheets
