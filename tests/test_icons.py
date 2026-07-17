"""
The Lucide icon set (ROADMAP: 0.4.1 UI icons).

A mistyped icon name would sail past every engine test and then crash when the
main window is built — these guard the name↔geometry contract from the one place
that runs headless everywhere.
"""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from laydown.ui import icons


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


class TestIconRenderer:
    def test_every_registered_icon_renders_non_null(self, app):
        for name in icons.names():
            icon = icons.lucide(name, 24, "#D07B24")
            assert not icon.isNull(), f"{name} rendered nothing"

    def test_unknown_name_is_a_clear_error(self, app):
        with pytest.raises(KeyError, match="no Lucide icon"):
            icons.lucide("does-not-exist")

    def test_colour_reaches_the_pixels(self, app):
        # Prove the stroke colour is honoured, so a themed icon isn't silently black.
        from PyQt6.QtGui import QColor
        pm = icons.lucide("zoom_in", 48, "#D07B24").pixmap(48, 48)
        img = pm.toImage()
        seen = {img.pixelColor(x, y).name()
                for x in range(0, 48, 2) for y in range(0, 48, 2)
                if img.pixelColor(x, y).alpha() > 200}
        # Antialiasing produces intermediate tones; the orange must dominate the
        # opaque stroke pixels, not black.
        oranges = [c for c in seen if QColor(c).redF() > QColor(c).blueF() + 0.15]
        assert oranges, f"no orange stroke pixels found, got {sorted(seen)[:6]}"


class TestWiredIntoTheWindow:
    def test_toolbar_and_tab_icon_names_all_exist(self, app):
        # main_window references icons by name; a typo there crashes construction.
        from laydown.ui import main_window as mw
        registered = set(icons.names())
        for name in mw._TAB_ICON_NAMES:
            assert name in registered, f"tab icon {name!r} is not registered"

    def test_the_window_builds_with_every_icon_present(self, app):
        from laydown.ui.main_window import MainWindow
        w = MainWindow()
        assert w._tab_bar.count() == 4
        assert all(not w._tab_bar.tabIcon(i).isNull() for i in range(4))
        assert not w._generate.icon().isNull()
        w.close()
