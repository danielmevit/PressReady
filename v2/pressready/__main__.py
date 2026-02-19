"""PressReady v2 entry point.  Run with: python -m pressready"""

import sys
import os

os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts.warning=false"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from pressready.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PressReady")
    app.setApplicationVersion("2.0.0")
    app.setFont(QFont("Segoe UI", 9))

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
