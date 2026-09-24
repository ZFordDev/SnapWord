"""Construction of auxiliary dock panels."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget

from .filetree import SnapWordFileTree


class FilesDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Files", parent)
        self.setObjectName("FileTreeDock")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.tree = SnapWordFileTree()
        self.setWidget(self.tree)
        self.hide()
