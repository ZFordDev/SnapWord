from .base import ToolbarSection


class ClearSection(ToolbarSection):
    key, title = "clear", "Reset"

    def __init__(self, editor, actions, parent=None):
        super().__init__(editor, actions, parent)
        self.command("format.clear", "Clear formatting", editor.clear_formatting, icon_text="Clear")
