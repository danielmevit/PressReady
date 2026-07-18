"""
Zoom must not spawn windows (0.4.2 bug).

Clicking zoom in/out rebuilds the preview grid. The old `_clear_grid` called
`setParent(None)` on each sheet widget, which reparents a visible child to the
desktop — turning it into a top-level window. Rapid zoom clicks then flashed
windows of the sheets ("opening new windows of the same app"). These pin that a
grid rebuild frees its widgets without ever making one top-level.
"""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QLabel

from laydown.ui.preview_panel import SheetCanvas


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def _populate(canvas, n=4):
    """Put n placeholder sheet widgets into the grid, as a render would."""
    from PyQt6.QtWidgets import QWidget
    widgets = []
    for i in range(n):
        w = QWidget(canvas._content)
        canvas._grid.addWidget(w, i // canvas._columns, i % canvas._columns)
        canvas._sheet_widgets.append(w)
        widgets.append(w)
    return widgets


class TestClearGridDoesNotOrphan:
    def test_clearing_the_grid_makes_no_top_level_widgets(self, app):
        canvas = SheetCanvas()
        canvas.show()
        widgets = _populate(canvas)

        canvas._clear_grid()

        # The reported bug: cleared sheet widgets became top-level windows.
        assert not any(w.parent() is None for w in widgets), (
            "a cleared sheet widget was reparented to top level (a new window)"
        )
        assert all(w.isHidden() for w in widgets), "cleared widgets should be hidden"

    def test_repeated_rebuilds_do_not_accumulate_windows(self, app):
        canvas = SheetCanvas()
        canvas.show()
        before = len(app.topLevelWidgets())
        for _ in range(6):            # like clicking zoom six times
            _populate(canvas)
            canvas._clear_grid()
        app.processEvents()           # let deleteLater run
        after = len(app.topLevelWidgets())
        assert after <= before, (
            f"top-level widgets grew {before} -> {after}; zoom is leaking windows"
        )
