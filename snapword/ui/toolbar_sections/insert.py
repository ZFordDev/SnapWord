from PySide6.QtWidgets import QInputDialog

from ..tablepicker import TablePickerDialog
from .base import ToolbarSection


class InsertSection(ToolbarSection):
    key, title = "insert", "Insert"

    def __init__(self, editor, actions, parent=None):
        super().__init__(editor, actions, parent)
        self.command("insert.link", "Insert link", self.link, icon_text="Link")
        self.command("insert.rule", "Horizontal rule", editor.insert_horizontal_rule, icon_text="Rule")
        self.command("insert.image", "Insert image", editor.insert_image_dialog, icon_text="Image")
        self.command("insert.table", "Insert table", self.table, icon_text="Table")

    def link(self):
        url, ok = QInputDialog.getText(self, "Insert Link", "URL:")
        if ok and url:
            text, ok = QInputDialog.getText(self, "Insert Link", "Display text (optional):")
            if ok:
                self.editor.insert_link(url, text)

    def table(self):
        dialog = TablePickerDialog(self)
        dialog.table_selected.connect(self.editor.insert_table)
        dialog.exec()
