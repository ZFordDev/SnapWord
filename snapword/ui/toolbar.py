"""Assemble independent toolbars without a hidden widget or duplicated actions."""

from PySide6.QtCore import QObject, Qt

from .toolbar_sections import SECTIONS


class ToolbarManager(QObject):
    # Two purposeful rows; advanced sections are available through View > Toolbars.
    DEFAULT_ROWS = (
        ("undo_redo", "font", "formatting", "alignment", "lists"),
        ("color", "indent", "spacing", "insert"),
    )

    def __init__(self, window, editor, actions):
        super().__init__(window)
        self.window = window
        self.sections = {section.key: section(editor, actions, window) for section in SECTIONS}
        self.action_print = actions["file.print"]
        self.action_export_pdf = actions["file.pdf"]
        self.action_insert_image = actions["insert.image"]
        self.action_insert_table = actions["insert.table"]
        self.reset()

    def reset(self):
        for bar in self.sections.values():
            self.window.removeToolBarBreak(bar)
            self.window.removeToolBar(bar)
        visible = {name for row in self.DEFAULT_ROWS for name in row}
        for index, row in enumerate(self.DEFAULT_ROWS):
            if index:
                self.window.addToolBarBreak(Qt.TopToolBarArea)
            for name in row:
                self.window.addToolBar(Qt.TopToolBarArea, self.sections[name])
                self.sections[name].show()
        for name, bar in self.sections.items():
            if name not in visible:
                self.window.addToolBar(Qt.TopToolBarArea, bar)
                bar.hide()

    def section_names(self):
        return list(self.sections)

    def toggle_section(self, name, visible):
        self.sections[name].setVisible(visible)

    def is_section_visible(self, name):
        return not self.sections[name].isHidden()

    def set_font_size(self, size):
        for bar in self.sections.values():
            bar.setStyleSheet(f"QToolBar QToolButton {{ font-size: {size}px; }}")
