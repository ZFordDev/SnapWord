from __future__ import annotations

from PySide6.QtCore import QDir, Signal
from PySide6.QtWidgets import QFileSystemModel, QTreeView


class SnapWordFileTree(QTreeView):
    file_opened = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("FileTreeList")

        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.currentPath())
        self.setModel(self.model)
        self.setRootIndex(self.model.index(QDir.currentPath()))

        self.setHeaderHidden(True)
        self.setMinimumWidth(220)

        for i in range(1, self.model.columnCount()):
            self.setColumnHidden(i, True)

        self.doubleClicked.connect(self._open_file)

    def _open_file(self, index) -> None:
        if self.model.fileInfo(index).isFile():
            self.file_opened.emit(self.model.filePath(index))
