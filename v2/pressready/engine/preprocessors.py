"""
Preprocessor pipeline — transforms applied to source pages before imposition.

Each preprocessor operates on a fitz.Document and returns a (possibly new) document.
The pipeline is: source PDF → preprocess chain → impose engine.
"""

import fitz
from typing import List

from pressready.engine.data_model import (
    PreprocessorStep,
    PreprocessorType,
    RotateAngle,
)


def apply_preprocessors(
    doc: fitz.Document,
    steps: List[PreprocessorStep],
) -> fitz.Document:
    """
    Apply a chain of preprocessor steps to *doc* (mutates in place).

    Returns the same document reference for convenience.
    """
    for step in steps:
        if not step.enabled:
            continue
        if step.type == PreprocessorType.ROTATE_PAGES:
            _rotate(doc, step.rotate_angle)
        elif step.type == PreprocessorType.SCALE_PAGES:
            _scale(doc, step.scale_factor)
        elif step.type == PreprocessorType.REORDER_PAGES:
            _reorder(doc, step.page_order)
    return doc


def _rotate(doc: fitz.Document, angle: RotateAngle) -> None:
    for page in doc:
        page.set_rotation((page.rotation + angle.value) % 360)


def _scale(doc: fitz.Document, factor: float) -> None:
    if factor == 1.0 or factor <= 0:
        return
    for page in doc:
        r = page.rect
        new_w = r.width * factor
        new_h = r.height * factor
        page.set_mediabox(fitz.Rect(0, 0, new_w, new_h))


def _reorder(doc: fitz.Document, order_expr: str) -> None:
    """
    Reorder pages.  Accepts:
      - "reverse"
      - comma-separated 1-based page numbers: "4,3,2,1"
    """
    expr = order_expr.strip().lower()
    if not expr:
        return

    n = len(doc)
    if expr == "reverse":
        new_order = list(range(n - 1, -1, -1))
    else:
        try:
            new_order = [int(x.strip()) - 1 for x in expr.split(",")]
        except ValueError:
            return  # silently skip bad expression
        if any(i < 0 or i >= n for i in new_order):
            return

    doc.select(new_order)
