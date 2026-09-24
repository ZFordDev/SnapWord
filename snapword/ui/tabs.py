from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut, QTextDocument
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTabBar, QWidget

from snapword.formats import load_as_html


@dataclass
class TabDocument:
    """State snapshot for a single open document."""

    path: str | None = None
    html: str = ""
    cursor_block: int = 0
    cursor_col: int = 0
    dirty: bool = False
    label: str = "Untitled"
    scroll: int = 0
    document: QTextDocument | None = None

    @staticmethod
    def from_path(path: str) -> TabDocument:
        try:
            html = load_as_html(path)
        except Exception:
            html = ""
        from pathlib import Path

        label = Path(path).name
        return TabDocument(path=path, html=html, label=label)


class _TabCloseButton(QPushButton):
    """Small x button embedded in each tab."""

    def __init__(self, parent=None) -> None:
        super().__init__("\u00d7", parent)
        self.setObjectName("TabCloseBtn")
        self.setFixedSize(18, 18)
        self.setCursor(Qt.PointingHandCursor)


class SnapWordTabBar(QWidget):
    """Tab bar with close buttons, dirty indicator, and a + button."""

    tab_changed = Signal(int)
    tab_close_requested = Signal(int)
    new_tab_requested = Signal()
    tab_moved = Signal(int, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("TabBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tab_bar = QTabBar()
        self._tab_bar.setMovable(True)
        self._tab_bar.setExpanding(False)
        self._tab_bar.setDrawBase(False)
        self._tab_bar.setObjectName("DocumentTabs")
        self._tab_bar.setTabsClosable(False)

        self._tab_bar.currentChanged.connect(self.tab_changed)
        self._tab_bar.tabMoved.connect(self.tab_moved)
        layout.addWidget(self._tab_bar, 1)

        self._add_btn = QPushButton("+")
        self._add_btn.setObjectName("NewTabButton")
        self._add_btn.setFixedSize(32, 28)
        self._add_btn.setToolTip("New document (Ctrl+T)")
        self._add_btn.setAccessibleName("New document")
        self._add_btn.clicked.connect(self.new_tab_requested)
        layout.addWidget(self._add_btn)

        self._new_tab_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        self._new_tab_shortcut.activated.connect(self.new_tab_requested)


    def add_tab(self, label: str) -> int:
        idx = self._tab_bar.addTab(label)
        self._tab_bar.setTabData(idx, {"label": label, "dirty": False})
        self._tab_bar.setTabToolTip(idx, label)
        self._sync_close_buttons()
        return idx

    def remove_tab(self, idx: int) -> None:
        if 0 <= idx < self._tab_bar.count():
            self._tab_bar.removeTab(idx)
            self._sync_close_buttons()

    def set_tab_label(self, idx: int, label: str) -> None:
        if 0 <= idx < self._tab_bar.count():
            data = self._tab_bar.tabData(idx) or {"dirty": False}
            data["label"] = label
            self._tab_bar.setTabData(idx, data)
            self._tab_bar.setTabText(idx, ("\u25cf " if data["dirty"] else "") + label)
            self._tab_bar.setTabToolTip(idx, label)

    def set_tab_dirty(self, idx: int, dirty: bool) -> None:
        if 0 <= idx < self._tab_bar.count():
            data = self._tab_bar.tabData(idx)
            data["dirty"] = dirty
            self._tab_bar.setTabData(idx, data)
            label = data["label"]
            prefix = "\u25cf " if dirty else ""
            self._tab_bar.setTabText(idx, prefix + label)

    def set_current_index(self, idx: int) -> None:
        if 0 <= idx < self._tab_bar.count():
            self._tab_bar.setCurrentIndex(idx)

    def current_index(self) -> int:
        return self._tab_bar.currentIndex()

    def count(self) -> int:
        return self._tab_bar.count()

    def _sync_close_buttons(self) -> None:
        for i in range(self._tab_bar.count()):
            if self._tab_bar.tabButton(i, QTabBar.ButtonPosition.RightSide) is not None:
                continue
            btn = _TabCloseButton(self._tab_bar)
            btn.setToolTip("Close document")
            btn.setAccessibleName("Close document")
            btn.clicked.connect(lambda _checked=False, button=btn: self._close_button_clicked(button))
            self._tab_bar.setTabButton(i, QTabBar.ButtonPosition.RightSide, btn)

    def _close_button_clicked(self, button) -> None:
        for index in range(self.count()):
            if self._tab_bar.tabButton(index, QTabBar.ButtonPosition.RightSide) is button:
                self.tab_close_requested.emit(index)
                return
