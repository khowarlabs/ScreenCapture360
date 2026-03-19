"""
Screen Recorder — Entry Point
"""
import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("ScreenCapture360")
    app.setOrganizationName("KhowarLabs")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
