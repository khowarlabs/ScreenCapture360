"""
ui/screen_selector.py
Modal dialog that lets the user choose either a monitor or an application
window to record.
"""
import mss
import pygetwindow as gw
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QImage
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class ScreenSelectorDialog(QDialog):
    """
    Two-tab dialog:
        • Monitors tab  — lists all displays detected by mss
        • Windows tab   — lists all visible application windows
    On accept, call `.get_selection()` to retrieve the config dict.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select Screen or Window")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        self._selection: dict | None = None
        self._build_ui()
        self._load_monitors()
        self._load_windows()

    # ------------------------------------------------------------------ #
    # UI construction                                                      #
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        headline = QLabel("Choose what you want to record:")
        headline.setObjectName("selectorHeadline")
        layout.addWidget(headline)

        self._tabs = QTabWidget()
        self._tabs.setObjectName("selectorTabs")

        # Thumbnail size configuration
        self._thumb_width = 180
        self._thumb_height = 110
        list_icon_size = QSize(self._thumb_width, self._thumb_height)

        # Monitors tab
        monitor_widget = QWidget()
        monitor_layout = QVBoxLayout(monitor_widget)
        self._monitor_list = QListWidget()
        self._monitor_list.setObjectName("monitorList")
        self._monitor_list.setIconSize(list_icon_size)
        self._monitor_list.setSpacing(4)
        monitor_layout.addWidget(self._monitor_list)
        self._tabs.addTab(monitor_widget, "🖥  Monitors")

        # Windows tab
        window_widget = QWidget()
        window_layout = QVBoxLayout(window_widget)
        self._window_list = QListWidget()
        self._window_list.setObjectName("windowList")
        self._window_list.setIconSize(list_icon_size)
        self._window_list.setSpacing(4)
        window_layout.addWidget(self._window_list)
        self._tabs.addTab(window_widget, "🪟  Application Windows")

        layout.addWidget(self._tabs)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ------------------------------------------------------------------ #
    # Data loading                                                         #
    # ------------------------------------------------------------------ #

    def _get_thumbnail(self, sct, region: dict) -> QIcon:
        """Capture a screenshot of a region and return it as a QIcon."""
        try:
            screenshot = sct.grab(region)
            # screenshot.rgb is raw RGB bytes
            img = QImage(
                screenshot.rgb, 
                screenshot.width, 
                screenshot.height, 
                QImage.Format.Format_RGB888
            )
            pixmap = QPixmap.fromImage(img)
            scaled = pixmap.scaled(
                self._thumb_width, 
                self._thumb_height, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            return QIcon(scaled)
        except Exception:
            return QIcon()

    def _load_monitors(self) -> None:
        with mss.mss() as sct:
            # sct.monitors[0] is the combined virtual screen — skip it
            for idx, mon in enumerate(sct.monitors[1:], start=1):
                label = (
                    f"Monitor {idx}  —  "
                    f"{mon['width']} × {mon['height']}  "
                    f"at ({mon['left']}, {mon['top']})"
                )
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, mon)
                
                # Add thumbnail
                icon = self._get_thumbnail(sct, mon)
                item.setIcon(icon)
                
                self._monitor_list.addItem(item)

        if self._monitor_list.count():
            self._monitor_list.setCurrentRow(0)

    def _load_windows(self) -> None:
        with mss.mss() as sct:
            all_windows = gw.getAllWindows()
            # De-duplicate while preserving order, and only keep visible windows with titles
            seen: set[str] = set()
            for win in all_windows:
                if not win.title.strip() or win.title in seen:
                    continue
                if win.width <= 0 or win.height <= 0:
                    continue
                
                seen.add(win.title)
                item = QListWidgetItem(win.title)
                
                # Add thumbnail
                region = {
                    "left": win.left,
                    "top": win.top,
                    "width": win.width,
                    "height": win.height
                }
                icon = self._get_thumbnail(sct, region)
                item.setIcon(icon)
                
                self._window_list.addItem(item)

        if self._window_list.count():
            self._window_list.setCurrentRow(0)

    # ------------------------------------------------------------------ #
    # Accept / result                                                      #
    # ------------------------------------------------------------------ #

    def _on_accept(self) -> None:
        tab_index = self._tabs.currentIndex()

        if tab_index == 0:
            # Monitor selected
            item = self._monitor_list.currentItem()
            if item is None:
                return
            self._selection = {
                "type": "monitor",
                "monitor": item.data(Qt.ItemDataRole.UserRole),
            }
        else:
            # Window selected
            item = self._window_list.currentItem()
            if item is None:
                return
            self._selection = {
                "type": "window",
                "window_title": item.text(),
            }

        self.accept()

    def get_selection(self) -> dict | None:
        """Return the user's selection dict, or None if cancelled."""
        return self._selection
