from .base import ToolbarSection


class ScriptSection(ToolbarSection):
    key, title = "super_sub", "Script"

    def __init__(self, editor, actions, parent=None):
        super().__init__(editor, actions, parent)
        self._checks = []
        for name, label, icon in (
            ("superscript", "Superscript", "X²"),
            ("subscript", "Subscript", "X₂"),
        ):
            action = self.command(
                f"format.{name}",
                label,
                getattr(editor, f"set_{name}"),
                checkable=True,
                icon_text=icon,
            )
            self._checks.append((action, getattr(editor, f"is_{name}")))
        editor.cursor_format_changed.connect(self.sync)
        self.sync()

    def sync(self):
        for action, query in self._checks:
            action.setChecked(query())
