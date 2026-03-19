"""
ui/main_window.py
Primary application window.  Hosts the Start Recording button and orchestrates
the screen selector dialog, the recorder thread, and the floating controls.
"""
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QLinearGradient, QColor, QPalette
from PyQt6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.recorder import RecorderThread
from ui.floating_controls import FloatingControls
from ui.screen_selector import ScreenSelectorDialog


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Screen Recorder")
        self.setMinimumSize(420, 320)
        self.resize(480, 340)

        self._recorder: RecorderThread | None = None
        self._floating: FloatingControls | None = None

        self._build_ui()
        self._apply_stylesheet()

    # ------------------------------------------------------------------ #
    # UI construction                                                      #
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # App icon / hero label
        icon_label = QLabel("⏺")
        icon_label.setObjectName("heroIcon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Title
        title = QLabel("Screen Recorder")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Capture your screen or any application window")
        subtitle.setObjectName("appSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        # Start button
        self._start_btn = QPushButton("⏺  Start Recording")
        self._start_btn.setObjectName("startBtn")
        self._start_btn.setFixedSize(220, 48)
        self._start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._start_btn.clicked.connect(self._on_start_clicked)
        layout.addWidget(self._start_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Status label (hidden by default)
        self._status_label = QLabel("")
        self._status_label.setObjectName("statusLabel")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

    def _apply_stylesheet(self) -> None:
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #0f0f1a;
            }
            QLabel#heroIcon {
                font-size: 52px;
                color: #e84855;
            }
            QLabel#appTitle {
                font-size: 26px;
                font-weight: 700;
                color: #f0f0f5;
            }
            QLabel#appSubtitle {
                font-size: 13px;
                color: #8888aa;
            }
            QPushButton#startBtn {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e84855, stop:1 #c0392b
                );
                color: #ffffff;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }
            QPushButton#startBtn:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff5f6d, stop:1 #d44033
                );
            }
            QPushButton#startBtn:pressed {
                background: #a93226;
            }
            QPushButton#startBtn:disabled {
                background: #444455;
                color: #888898;
            }
            QLabel#statusLabel {
                font-size: 12px;
                color: #55cc88;
                padding: 4px 12px;
            }
        """)

    # ------------------------------------------------------------------ #
    # Start recording flow                                                 #
    # ------------------------------------------------------------------ #

    def _on_start_clicked(self) -> None:
        dialog = ScreenSelectorDialog(self)
        if dialog.exec() != ScreenSelectorDialog.DialogCode.Accepted:
            return

        selection = dialog.get_selection()
        if not selection:
            return

        self._start_recorder(selection)

    def _start_recorder(self, config: dict) -> None:
        # Create and wire up recorder thread
        self._recorder = RecorderThread(capture_config=config, fps=15, parent=self)
        self._recorder.finished.connect(self._on_recording_finished)
        self._recorder.error.connect(self._on_recording_error)

        # Create and position floating controls (bottom-centre of screen)
        self._floating = FloatingControls()
        self._floating.pause_requested.connect(self._recorder.pause)
        self._floating.resume_requested.connect(self._recorder.resume)
        self._floating.mic_toggled.connect(self._recorder.toggle_mic)
        self._floating.stop_requested.connect(self._stop_recording)

        # Position the floating panel near the bottom-centre of the primary screen
        from PyQt6.QtWidgets import QApplication
        screen_geo = QApplication.primaryScreen().availableGeometry()
        fx = screen_geo.center().x() - self._floating.width() // 2
        fy = screen_geo.bottom() - self._floating.height() - 40
        self._floating.move(fx, fy)
        self._floating.show()

        # Disable start button while recording
        self._start_btn.setEnabled(False)
        self._status_label.setText("Recording in progress…")

        self._recorder.start()

    # ------------------------------------------------------------------ #
    # Stop / finish flow                                                   #
    # ------------------------------------------------------------------ #

    def _stop_recording(self) -> None:
        if self._recorder:
            self._recorder.stop_recording()
        if self._floating:
            self._floating.close()
            self._floating = None

    def _on_recording_finished(self, file_path: str) -> None:
        self._start_btn.setEnabled(True)
        self._status_label.setText(f"✅  Saved to: {file_path}")
        self._recorder = None

    def _on_recording_error(self, message: str) -> None:
        if self._floating:
            self._floating.close()
            self._floating = None
        self._start_btn.setEnabled(True)
        self._status_label.setText("")
        QMessageBox.critical(self, "Recording Error", message)
        self._recorder = None

    # ------------------------------------------------------------------ #
    # Close guard                                                          #
    # ------------------------------------------------------------------ #

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._recorder and self._recorder.isRunning():
            self._stop_recording()
            self._recorder.wait(3000)
        event.accept()
