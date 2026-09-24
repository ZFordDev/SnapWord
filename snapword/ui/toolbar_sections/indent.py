from .base import ToolbarSection


class IndentSection(ToolbarSection):
    key, title = "indent", "Indent"

    def __init__(self, editor, actions, parent=None):
        super().__init__(editor, actions, parent)
        self.command("paragraph.indent", "Increase indent", editor.set_indent, icon_text="→")
        self.command("paragraph.outdent", "Decrease indent", editor.set_outdent, icon_text="←")
