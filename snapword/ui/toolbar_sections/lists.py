from .base import ToolbarSection


class ListsSection(ToolbarSection):
    key, title = "lists", "Lists"

    def __init__(self, editor, actions, parent=None):
        super().__init__(editor, actions, parent)
        self.command("paragraph.bullets", "Bullet list", editor.set_bullet_list, icon_text="• List")
        self.command("paragraph.numbers", "Numbered list", editor.set_numbered_list, icon_text="1. List")
