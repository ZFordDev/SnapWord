from .base import ToolbarSection


class BlocksSection(ToolbarSection):
    key, title = "blocks", "Blocks"

    def __init__(self, editor, actions, parent=None):
        super().__init__(editor, actions, parent)
        self.command("paragraph.quote", "Block quote", editor.set_block_quote, icon_text="Quote")
        self.command("paragraph.code", "Code block", editor.set_code_block, icon_text="Code")
