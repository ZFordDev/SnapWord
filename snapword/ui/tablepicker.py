from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class _GridCell(QPushButton):
    """A single cell in the table picker grid."""

    hovered = Signal(int, int)

    def __init__(self, row: int, col: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.row = row
        self.col = col
        self.setFixedSize(22, 22)
        self.setCheckable(True)
        self.setStyleSheet(
            "QPushButton { border: 1px solid #bbb; background: #fff; margin: 0; padding: 0; }"
            "QPushButton:hover { border: 1px solid #4aa3ff; background: #e8f0fe; }"
        )

    def enterEvent(self, event) -> None:  # noqa: N802
        self.hovered.emit(self.row, self.col)
        super().enterEvent(event)


class TablePickerDialog(QDialog):
    """A Google Docs-style grid picker for selecting table dimensions.

    Emits ``table_selected(rows, cols)`` when the user clicks a cell.
    """

    table_selected = Signal(int, int)

    MAX_ROWS = 10
    MAX_COLS = 8

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Insert Table")
        self.setFixedSize(340, 300)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)

        # Dimension label
        self._label = QLabel("Insert table")
        root.addWidget(self._label)

        # Grid
        grid_widget = QWidget()
        self._grid = QGridLayout(grid_widget)
        self._grid.setSpacing(2)
        self._grid.setContentsMargins(0, 0, 0, 0)

        self._cells: list[list[_GridCell]] = []
        for r in range(self.MAX_ROWS):
            row_cells: list[_GridCell] = []
            for c in range(self.MAX_COLS):
                cell = _GridCell(r, c)
                cell.hovered.connect(self._on_hover)
                cell.clicked.connect(self._on_click)
                self._grid.addWidget(cell, r, c)
                row_cells.append(cell)
            self._cells.append(row_cells)

        root.addWidget(grid_widget)

        # Preset buttons
        presets = QHBoxLayout()
        for label, r, c in [("2×2", 2, 2), ("3×3", 3, 3), ("5×5", 5, 5)]:
            btn = QPushButton(label)
            btn.setFixedHeight(26)
            btn.clicked.connect(lambda checked=False, rr=r, cc=c: self._emit(rr, cc))
            presets.addWidget(btn)
        presets.addStretch()
        root.addLayout(presets)

        self._selected_row = 0
        self._selected_col = 0

    def _on_hover(self, row: int, col: int) -> None:
        self._selected_row = row
        self._selected_col = col
        self._label.setText(f"{row + 1} × {col + 1} table")

        # Highlight cells up to (row, col)
        for r in range(self.MAX_ROWS):
            for c in range(self.MAX_COLS):
                cell = self._cells[r][c]
                if r <= row and c <= col:
                    cell.setStyleSheet(
                        "QPushButton { border: 1px solid #4aa3ff; background: #d2e3fc; margin: 0; padding: 0; }"
                    )
                else:
                    cell.setStyleSheet(
                        "QPushButton { border: 1px solid #bbb; background: #fff; margin: 0; padding: 0; }"
                        "QPushButton:hover { border: 1px solid #4aa3ff; background: #e8f0fe; }"
                    )

    def _on_click(self) -> None:
        self._emit(self._selected_row + 1, self._selected_col + 1)

    def _emit(self, rows: int, cols: int) -> None:
        self.table_selected.emit(rows, cols)
        self.accept()
