"""PressReady v2 entry point.  Run with: python -m pressready"""

import sys
import os
import ctypes

os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts.warning=false"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from pressready.ui.main_window import MainWindow, _app_icon


def main():
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("pressready.v2")

    app = QApplication(sys.argv)
    app.setApplicationName("PressReady")
    app.setApplicationVersion("2.0.0")
    app.setWindowIcon(_app_icon())
    app.setFont(QFont("Segoe UI", 9))

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
