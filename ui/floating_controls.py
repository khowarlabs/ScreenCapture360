"""
ui/floating_controls.py
Always-on-top frameless popup panel shown during recording.
Provides Pause/Resume and Stop controls and a pulsing REC indicator.
"""
from PyQt6.QtCore import QPropertyAnimation, QRect, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QPushButton, QWidget


class FloatingControls(QWidget):
    """
    Frameless, always-on-top compact control strip.
    Signals:
        pause_requested  — user wants to pause
        resume_requested — user wants to resume
        stop_requested   — user wants to stop recording
        mic_toggled(bool) — user toggled microphone on/off
    """

    pause_requested = pyqtSignal()
    resume_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    mic_toggled = pyqtSignal(bool)

    # ------------------------------------------------------------------ #
    # Construction                                                         #
    # ------------------------------------------------------------------ #

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._paused = False
        self._mic_enabled = True
        self._drag_pos = None

        # Window flags: frameless, always on top, tool window (no taskbar entry)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(280, 40)

        self._build_ui()
        self._setup_pulse_timer()

    # ------------------------------------------------------------------ #
    # UI construction                                                      #
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        # Pulsing REC dot
        self._rec_indicator = QWidget()
        self._rec_indicator.setFixedSize(12, 12)
        self._rec_indicator.setObjectName("recDot")
        layout.addWidget(self._rec_indicator)

        self._rec_label = QLabel("REC")
        self._rec_label.setObjectName("recLabel")
        layout.addWidget(self._rec_label)

        layout.addStretch()

        # Mic button
        self._mic_btn = QPushButton("🎙️")
        self._mic_btn.setObjectName("controlBtn")
        self._mic_btn.setToolTip("Toggle Microphone")
        self._mic_btn.setFixedSize(30, 30)
        self._mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mic_btn.clicked.connect(self._on_mic_toggle)
        layout.addWidget(self._mic_btn)

        # Pause / Resume button
        self._pause_btn = QPushButton("⏸")
        self._pause_btn.setObjectName("controlBtn")
        self._pause_btn.setToolTip("Pause Recording")
        self._pause_btn.setFixedSize(30, 30)
        self._pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pause_btn.clicked.connect(self._on_pause_resume)
        layout.addWidget(self._pause_btn)

        # Stop button
        stop_btn = QPushButton("⏹")
        stop_btn.setObjectName("stopBtn")
        stop_btn.setToolTip("Stop Recording")
        stop_btn.setFixedSize(30, 30)
        stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        stop_btn.clicked.connect(self.stop_requested)
        layout.addWidget(stop_btn)

        self._apply_stylesheet()

    def _apply_stylesheet(self) -> None:
        self.setStyleSheet("""
            QWidget#recDot {
                background-color: #ff4d4d;
                border-radius: 6px;
            }
            QLabel#recLabel {
                color: #ffffff;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 1px;
            }
            QPushButton#controlBtn {
                background: rgba(255, 255, 255, 0.12);
                color: #ffffff;
                border: 1px solid rgba(255,255,255,0.20);
                border-radius: 15px;
                font-size: 14px;
            }
            QPushButton#controlBtn:hover {
                background: rgba(255, 255, 255, 0.25);
            }
            QPushButton#controlBtn[muted="true"] {
                color: #ff4d4d;
                background: rgba(255, 77, 77, 0.15);
                border-color: rgba(255, 77, 77, 0.30);
            }
            QPushButton#stopBtn {
                background: rgba(220, 53, 69, 0.85);
                color: #ffffff;
                border: none;
                border-radius: 15px;
                font-size: 14px;
            }
            QPushButton#stopBtn:hover {
                background: #dc3545;
            }
        """)

    # ------------------------------------------------------------------ #
    # Interaction Handlers                                                 #
    # ------------------------------------------------------------------ #

    def _on_mic_toggle(self) -> None:
        self._mic_enabled = not self._mic_enabled
        self._mic_btn.setProperty("muted", "true" if not self._mic_enabled else "false")
        self._mic_btn.setText("🎙️" if self._mic_enabled else "🔇")
        self._mic_btn.style().unpolish(self._mic_btn)
        self._mic_btn.style().polish(self._mic_btn)
        self.mic_toggled.emit(self._mic_enabled)

    def _on_pause_resume(self) -> None:
        if self._paused:
            self._paused = False
            self._pause_btn.setText("⏸")
            self._pause_btn.setToolTip("Pause Recording")
            self.resume_requested.emit()
        else:
            self._paused = True
            self._pause_btn.setText("▶")
            self._pause_btn.setToolTip("Resume Recording")
            self.pause_requested.emit()

    # ------------------------------------------------------------------ #
    # Pulsing REC indicator                                                #
    # ------------------------------------------------------------------ #

    def _setup_pulse_timer(self) -> None:
        self._dot_visible = True
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse_dot)
        self._pulse_timer.start(600)

    def _pulse_dot(self) -> None:
        if self._paused:
            self._rec_indicator.setStyleSheet("background-color: #f0a500; border-radius: 6px;")
            self._rec_label.setText("PAUSED")
            return

        self._dot_visible = not self._dot_visible
        opacity = "1.0" if self._dot_visible else "0.2"
        self._rec_indicator.setStyleSheet(f"background-color: rgba(255, 77, 77, {opacity}); border-radius: 6px;")
        self._rec_label.setText("REC")

    # ------------------------------------------------------------------ #
    # Custom Background & Dragging                                         #
    # ------------------------------------------------------------------ #

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)
        painter.fillPath(path, QColor(15, 15, 25, 235))
        super().paintEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_pos = None
