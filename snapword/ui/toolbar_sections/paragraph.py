from PySide6.QtCore import Qt
from PySide6.QtGui import QActionGroup

from .base import ToolbarSection


class AlignmentSection(ToolbarSection):
    key, title = "alignment", "Alignment"

    def __init__(self, editor, actions, parent=None):
        super().__init__(editor, actions, parent)
        self.group = QActionGroup(self)
        self._alignments = []
        for name, alignment in (
            ("Left", Qt.AlignLeft),
            ("Center", Qt.AlignHCenter),
            ("Right", Qt.AlignRight),
            ("Justify", Qt.AlignJustify),
        ):
            action = self.command(
                f"paragraph.{name.lower()}",
                f"Align {name.lower()}",
                lambda checked=False, value=alignment: editor.set_alignment(value),
                checkable=True,
                icon_text=name,
            )
            self.group.addAction(action)
            self._alignments.append((action, alignment))
        editor.cursor_format_changed.connect(self.sync)
        self.sync()

    def sync(self):
        for action, alignment in self._alignments:
            action.setChecked(bool(self.editor.alignment() & alignment))
