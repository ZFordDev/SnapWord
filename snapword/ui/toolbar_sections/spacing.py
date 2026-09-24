from PySide6.QtCore import QSignalBlocker
from PySide6.QtGui import QTextBlockFormat
from PySide6.QtWidgets import QComboBox

from .base import ToolbarSection


class SpacingSection(ToolbarSection):
    key, title = "spacing", "Spacing"

    def __init__(self, editor, actions, parent=None):
        super().__init__(editor, actions, parent)
        self.combo = QComboBox(self)
        self.combo.setAccessibleName("Line spacing")
        self.combo.setToolTip("Line spacing")
        for value in (1.0, 1.15, 1.5, 2.0):
            self.combo.addItem(f"{value:g}", value)
        self.addWidget(self.combo)
        self.combo.activated.connect(lambda index: editor.set_line_spacing(self.combo.itemData(index)))
        editor.cursor_format_changed.connect(self.sync)
        self.sync()

    def sync(self):
        fmt = self.editor.textCursor().blockFormat()
        proportional = QTextBlockFormat.LineHeightTypes.ProportionalHeight.value
        spacing = fmt.lineHeight() / 100 if fmt.lineHeightType() == proportional else 1.0
        with QSignalBlocker(self.combo):
            self.combo.setCurrentIndex(self.combo.findData(spacing))
