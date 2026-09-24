import math

from PySide6.QtCore import QSignalBlocker
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QComboBox, QFontComboBox

from .base import ToolbarSection


class FontSection(ToolbarSection):
    key, title = "font", "Font"

    def __init__(self, editor, actions, parent=None):
        super().__init__(editor, actions, parent)
        self.family = QFontComboBox(self)
        self.family.setMaximumWidth(160)
        self.family.setAccessibleName("Font family")
        self.size = QComboBox(self)
        self.size.setEditable(True)
        self.size.setFixedWidth(68)
        self.size.setAccessibleName("Font size")
        self.size.addItems([str(s) for s in (8, 9, 10, 10.5, 11, 12, 14, 16, 18, 24, 36, 48, 72)])
        self.addWidget(self.family)
        self.addWidget(self.size)
        self.family.currentFontChanged.connect(lambda font: editor.set_font_family(font.family()))
        self.size.activated.connect(self.apply_size)
        self.size.lineEdit().editingFinished.connect(self.apply_size)
        editor.cursor_format_changed.connect(self.sync)
        self.sync()

    def apply_size(self, *_):
        try:
            size = float(self.size.currentText())
        except ValueError:
            self.sync()
            return
        if math.isfinite(size) and 1 <= size <= 512:
            self.editor.set_font_size(size)
        self.sync()

    def sync(self):
        size = self.editor.current_font_size()
        font = QFont(self.editor.current_font_family())
        font.setPointSizeF(size)
        with QSignalBlocker(self.family), QSignalBlocker(self.size):
            self.family.setCurrentFont(font)
            self.size.setCurrentText(f"{size:g}")
