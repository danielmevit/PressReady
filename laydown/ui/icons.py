"""
UI icons — the Lucide icon set (https://lucide.dev), rendered through Qt.

Lucide is ISC-licensed; see NOTICE. Each icon below is the *verbatim* inner geometry
of the corresponding Lucide SVG (v1.24.0) — pulled from the `lucide-static` package,
not redrawn — so they match the published icons exactly. They are wrapped at render
time in an <svg> with the theme stroke colour and rasterised with QtSvg.

Add an icon: copy the inner markup of its Lucide SVG into _GEOMETRY under a new key.
"""

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QIcon, QImage, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

from laydown.ui import theme as t

# Verbatim inner geometry of each Lucide icon (v1.24.0, ISC). Key = our name.
_GEOMETRY = {
    'columns_1': '<rect width="12" height="20" x="6" y="2" rx="2" />',
    'columns_2': '<rect width="18" height="18" x="3" y="3" rx="2" /> <path d="M12 3v18" />',
    'columns_4': '<path d="M12 3v18" /> <path d="M3 12h18" /> <rect x="3" y="3" width="18" height="18" rx="2" />',
    'zoom_in': '<circle cx="11" cy="11" r="8" /> <line x1="21" x2="16.65" y1="21" y2="16.65" /> <line x1="11" x2="11" y1="8" y2="14" /> <line x1="8" x2="14" y1="11" y2="11" />',
    'zoom_out': '<circle cx="11" cy="11" r="8" /> <line x1="21" x2="16.65" y1="21" y2="16.65" /> <line x1="8" x2="14" y1="11" y2="11" />',
    'fit_width': '<path d="m18 8 4 4-4 4" /> <path d="M2 12h20" /> <path d="m6 8-4 4 4 4" />',
    'fit_page': '<path d="M8 3H5a2 2 0 0 0-2 2v3" /> <path d="M21 8V5a2 2 0 0 0-2-2h-3" /> <path d="M3 16v3a2 2 0 0 0 2 2h3" /> <path d="M16 21h3a2 2 0 0 0 2-2v-3" />',
    'actual_size': '<path d="M3 7V5a2 2 0 0 1 2-2h2" /> <path d="M17 3h2a2 2 0 0 1 2 2v2" /> <path d="M21 17v2a2 2 0 0 1-2 2h-2" /> <path d="M7 21H5a2 2 0 0 1-2-2v-2" />',
    'tab_source': '<path d="M4 11V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.706.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-1" /> <path d="M14 2v5a1 1 0 0 0 1 1h5" /> <path d="M2 15h10" /> <path d="m9 18 3-3-3-3" />',
    'tab_layout': '<rect width="18" height="7" x="3" y="3" rx="1" /> <rect width="9" height="7" x="3" y="14" rx="1" /> <rect width="5" height="7" x="16" y="14" rx="1" />',
    'tab_sheet': '<path d="M21.3 15.3a2.4 2.4 0 0 1 0 3.4l-2.6 2.6a2.4 2.4 0 0 1-3.4 0L2.7 8.7a2.41 2.41 0 0 1 0-3.4l2.6-2.6a2.41 2.41 0 0 1 3.4 0Z" /> <path d="m14.5 12.5 2-2" /> <path d="m11.5 9.5 2-2" /> <path d="m8.5 6.5 2-2" /> <path d="m17.5 15.5 2-2" />',
    'tab_marks': '<path d="M6 2v14a2 2 0 0 0 2 2h14" /> <path d="M18 22V8a2 2 0 0 0-2-2H2" />',
    'generate': '<path d="M4.226 20.925A2 2 0 0 0 6 22h12a2 2 0 0 0 2-2V8a2.4 2.4 0 0 0-.706-1.706l-3.588-3.588A2.4 2.4 0 0 0 14 2H6a2 2 0 0 0-2 2v3.127" /> <path d="M14 2v5a1 1 0 0 0 1 1h5" /> <path d="m5 11-3 3" /> <path d="m5 17-3-3h10" />',
}

# Lucide's canvas and stroke conventions — do not change per-icon, that's the point.
_VIEWBOX = 24
_STROKE_WIDTH = 2.0

_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vb} {vb}" fill="none" '
    'stroke="{color}" stroke-width="{sw}" stroke-linecap="round" '
    'stroke-linejoin="round">{inner}</svg>'
)


def lucide(name: str, size: int = 22, color: str | None = None,
           stroke_width: float = _STROKE_WIDTH) -> QIcon:
    """A Lucide icon as a QIcon, stroked in *color* (defaults to muted foreground)."""
    if name not in _GEOMETRY:
        raise KeyError(f"no Lucide icon registered as {name!r}")
    svg = _SVG.format(vb=_VIEWBOX, color=color or t.FG_MUTED,
                      sw=stroke_width, inner=_GEOMETRY[name]).encode("utf-8")

    # Render at 3x for crisp edges on any DPI, then tag the pixmap's ratio so Qt
    # draws it at the logical size.
    scale = 3
    renderer = QSvgRenderer(svg)
    image = QImage(size * scale, size * scale, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size * scale, size * scale))
    painter.end()

    pixmap = QPixmap.fromImage(image)
    pixmap.setDevicePixelRatio(scale)
    return QIcon(pixmap)


def names() -> tuple:
    """Every registered icon name — used by the test that guards the set."""
    return tuple(_GEOMETRY)
