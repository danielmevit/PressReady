"""
PressReady entry point.

Run with: python -m pressready
"""

import sys
import os

# Suppress Qt font warnings on Windows
os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts.warning=false"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from pressready.ui.main_window import MainWindow


def main():
    """Launch PressReady application."""
    app = QApplication(sys.argv)
    app.setApplicationName("PressReady")
    app.setApplicationVersion("0.6.0")
    
    # Set default font to avoid MS Sans Serif fallback issues
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
