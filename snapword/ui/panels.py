"""Construction of auxiliary dock panels."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QHBoxLayout, QLineEdit, QToolButton, QVBoxLayout, QWidget

from .filetree import SnapWordFileTree


class FilesDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Files", parent)
        self.setObjectName("FileTreeDock")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.tree = SnapWordFileTree()
        self.up_button = QToolButton()
        self.up_button.setObjectName("FileTreeUpButton")
        self.up_button.setText("Up")
        self.up_button.setToolTip("Go to parent folder")
        self.path_display = QLineEdit()
        self.path_display.setObjectName("FileTreePath")
        self.path_display.setReadOnly(True)
        self.path_display.setToolTip(self.tree.model.rootPath())

        controls = QHBoxLayout()
        controls.setContentsMargins(6, 6, 6, 0)
        controls.addWidget(self.up_button)
        controls.addWidget(self.path_display, 1)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(controls)
        layout.addWidget(self.tree, 1)
        self.setWidget(container)

        self.up_button.clicked.connect(self.tree.navigate_up)
        self.tree.root_path_changed.connect(self._update_root_path)
        self._update_root_path(self.tree.model.rootPath())
        self.hide()

    def _update_root_path(self, path: str) -> None:
        self.path_display.setText(path)
        self.path_display.setCursorPosition(0)
        self.path_display.setToolTip(path)
        self.up_button.setEnabled(self.tree.can_navigate_up())
