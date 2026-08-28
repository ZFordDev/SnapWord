from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)


class FindReplaceBar(QWidget):
    """Floating search/replace bar that appears above the editor."""

    close_requested = Signal()

    def __init__(self, editor, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("FindReplaceBar")
        self._editor = editor
        self._replace_visible = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # Search input
        layout.addWidget(QLabel("Find:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setMinimumWidth(200)
        self.search_input.returnPressed.connect(self.find_next)
        self.search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_input)

        # Match case
        self.match_case = QCheckBox("Aa")
        self.match_case.setToolTip("Match case")
        layout.addWidget(self.match_case)

        # Find prev/next
        self.btn_prev = QPushButton("\u25b2")
        self.btn_prev.setFixedSize(28, 28)
        self.btn_prev.setToolTip("Previous (Shift+Enter)")
        self.btn_prev.clicked.connect(self.find_prev)
        layout.addWidget(self.btn_prev)

        self.btn_next = QPushButton("\u25bc")
        self.btn_next.setFixedSize(28, 28)
        self.btn_next.setToolTip("Next (Enter)")
        self.btn_next.clicked.connect(self.find_next)
        layout.addWidget(self.btn_next)

        # Result count
        self.result_label = QLabel("")
        self.result_label.setObjectName("FindResultLabel")
        layout.addWidget(self.result_label)

        layout.addStretch(1)

        # Replace section (hidden by default)
        self.replace_widget = QWidget()
        replace_layout = QHBoxLayout(self.replace_widget)
        replace_layout.setContentsMargins(0, 0, 0, 0)
        replace_layout.setSpacing(6)

        replace_layout.addWidget(QLabel("Replace:"))
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace with...")
        self.replace_input.setMinimumWidth(200)
        replace_layout.addWidget(self.replace_input)

        self.btn_replace = QPushButton("Replace")
        self.btn_replace.setFixedHeight(28)
        self.btn_replace.clicked.connect(self.replace_current)
        replace_layout.addWidget(self.btn_replace)

        self.btn_replace_all = QPushButton("All")
        self.btn_replace_all.setFixedHeight(28)
        self.btn_replace_all.setToolTip("Replace all")
        self.btn_replace_all.clicked.connect(self.replace_all)
        replace_layout.addWidget(self.btn_replace_all)

        layout.addWidget(self.replace_widget)
        self.replace_widget.hide()

        # Close button
        self.btn_close = QPushButton("\u00d7")
        self.btn_close.setFixedSize(28, 28)
        self.btn_close.setToolTip("Close (Esc)")
        self.btn_close.clicked.connect(self.close_requested.emit)
        layout.addWidget(self.btn_close)

        # Keyboard shortcuts
        self.search_input.installEventFilter(self)

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def show_replace(self) -> None:
        self._replace_visible = True
        self.replace_widget.show()
        self.search_input.setFocus()
        self.search_input.selectAll()

    def toggle_replace(self) -> None:
        if self._replace_visible:
            self._replace_visible = False
            self.replace_widget.hide()
        else:
            self.show_replace()

    def focus_search(self) -> None:
        self.search_input.setFocus()
        self.search_input.selectAll()

    # ---------------------------------------------------------
    # Find operations
    # ---------------------------------------------------------

    def find_next(self) -> None:
        text = self.search_input.text()
        if not text:
            return
        flags = QTextDocument.FindFlag(0)
        if self.match_case.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        if not self._editor.find(text, flags):
            # Wrap around to start
            cursor = self._editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self._editor.setTextCursor(cursor)
            self._editor.find(text, flags)

        self._update_result_count()

    def find_prev(self) -> None:
        text = self.search_input.text()
        if not text:
            return
        flags = QTextDocument.FindFlag.FindBackward
        if self.match_case.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        if not self._editor.find(text, flags):
            # Wrap around to end
            cursor = self._editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self._editor.setTextCursor(cursor)
            self._editor.find(text, flags)

        self._update_result_count()

    def replace_current(self) -> None:
        text = self.search_input.text()
        replace_text = self.replace_input.text()
        if not text:
            return

        cursor = self._editor.textCursor()
        if cursor.hasSelection() and cursor.selectedText() == text:
            cursor.insertText(replace_text)

        self.find_next()

    def replace_all(self) -> None:
        text = self.search_input.text()
        replace_text = self.replace_input.text()
        if not text:
            return

        cursor = self._editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        self._editor.setTextCursor(cursor)

        count = 0
        flags = QTextDocument.FindFlag(0)
        if self.match_case.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        while self._editor.find(text, flags):
            self._editor.textCursor().insertText(replace_text)
            count += 1

        self.result_label.setText(f"{count} replaced")

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _on_search_changed(self, text: str) -> None:
        if not text:
            self.result_label.setText("")
            return
        self._update_result_count()

    def _update_result_count(self) -> None:
        text = self.search_input.text()
        if not text:
            self.result_label.setText("")
            return

        # Count occurrences in the document
        flags = QTextDocument.FindFlag(0)
        if self.match_case.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        count = 0
        cursor = self._editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        self._editor.setTextCursor(cursor)

        while self._editor.find(text, flags):
            count += 1

        # Restore cursor to original position
        self._editor.setTextCursor(cursor)
        self.result_label.setText(f"{count} found" if count != 1 else "1 found")

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self.close_requested.emit()
        else:
            super().keyPressEvent(event)
