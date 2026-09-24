from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog

from .base import ToolbarSection


class ColorSection(ToolbarSection):
    key, title = "color", "Color"

    def __init__(self, editor, actions, parent=None):
        super().__init__(editor, actions, parent)
        self.command("format.color", "Text color", self.text_color, icon_text="Color")
        self.command("format.highlight", "Highlight color", self.highlight, icon_text="Highlight")

    def text_color(self):
        self._choose("Text color", self.editor.current_text_color(), "#202124", self.editor.set_text_color)

    def highlight(self):
        self._choose(
            "Highlight color", self.editor.current_highlight_color(), "#ffff00", self.editor.set_highlight_color
        )

    def _choose(self, title, current, fallback, setter):
        color = QColorDialog.getColor(current or QColor(fallback), self, title)
        if color.isValid():
            setter(color)
