from .base import ToolbarSection


class TextSection(ToolbarSection):
    key, title = "formatting", "Text"

    def __init__(self, editor, actions, parent=None):
        super().__init__(editor, actions, parent)
        self._checks = []
        for name, label, icon, shortcut in (
            ("bold", "Bold", "B", "Ctrl+B"),
            ("italic", "Italic", "I", "Ctrl+I"),
            ("underline", "Underline", "U", "Ctrl+U"),
            ("strikethrough", "Strikethrough", "S", None),
        ):
            action = self.command(
                f"format.{name}",
                label,
                getattr(editor, f"set_{name}"),
                checkable=True,
                shortcut=shortcut,
                icon_text=icon,
            )
            font = action.font()
            if name == "bold":
                font.setBold(True)
            elif name == "italic":
                font.setItalic(True)
            elif name == "underline":
                font.setUnderline(True)
            else:
                font.setStrikeOut(True)
            action.setFont(font)
            self._checks.append((action, getattr(editor, f"is_{name}")))
        editor.cursor_format_changed.connect(self.sync)
        self.sync()

    def sync(self):
        for action, query in self._checks:
            action.setChecked(query())
