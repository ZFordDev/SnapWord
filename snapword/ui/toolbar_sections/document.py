from .base import ToolbarSection


class DocumentSection(ToolbarSection):
    key, title = "export", "Document"

    def __init__(self, editor, actions, parent=None):
        super().__init__(editor, actions, parent)
        self.command("file.print", "Print", editor.print_document, shortcut="Ctrl+P")
        self.command("file.pdf", "Export as PDF", editor.export_pdf, shortcut="Ctrl+Shift+P", icon_text="PDF")
