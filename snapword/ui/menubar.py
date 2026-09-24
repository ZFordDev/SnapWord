"""Menu placement for shared commands; behavior lives in controllers/sections."""
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QMenuBar


class SnapWordMenuBar(QMenuBar):
    def __init__(self, actions, parent=None):
        super().__init__(parent)
        self.registry = actions
        self.file_menu = self.addMenu("File")
        self._fill(self.file_menu, ("file.new", "file.open", "file.folder", None, "file.save", "file.save_as",
                                    None, "file.print"))
        export = self.file_menu.addMenu("Export")
        self._fill(export, ("file.pdf", "file.rtf", "file.txt", "file.html", "file.md"))
        edit = self.addMenu("Edit")
        self._fill(edit, ("edit.undo", "edit.redo", None, "edit.find", "edit.replace", None, "edit.preferences"))
        insert = self.addMenu("Insert")
        self._fill(insert, ("insert.link", "insert.image", "insert.table", "insert.rule"))
        format_menu = self.addMenu("Format")
        self._fill(format_menu, (
            "format.bold", "format.italic", "format.underline", "format.strikethrough",
            "format.superscript", "format.subscript", None, "format.color", "format.highlight",
            None, "paragraph.left", "paragraph.center", "paragraph.right", "paragraph.justify",
            None, "paragraph.bullets", "paragraph.numbers", "paragraph.indent", "paragraph.outdent",
            "paragraph.quote", "paragraph.code", None, "format.clear",
        ))
        self.view_menu = self.addMenu("View")
        self.toolbar_menu = self.view_menu.addMenu("Toolbars")
        self._fill(self.view_menu, ("view.reset",))
        self._theme_menu = self.view_menu.addMenu("Theme")
        self._theme_group = QActionGroup(self)
        self._user_theme_actions = []
        for key in ("theme.light", "theme.dark"):
            self._theme_menu.addAction(actions[key])
            self._theme_group.addAction(actions[key])
        self._theme_menu.addSeparator()
        self._theme_menu.addAction(actions["theme.edit"])
        # Existing integrations may still refer to these named actions.
        self.action_print = actions["file.print"]
        self.action_export_pdf = actions["file.pdf"]
        self.action_theme_edit = actions["theme.edit"]
        self.action_preferences = actions["edit.preferences"]
        self.action_reset_layout = actions["view.reset"]

    def _fill(self, menu, keys):
        for key in keys:
            if key is None:
                menu.addSeparator()
            else:
                menu.addAction(self.registry[key])

    def add_user_theme_action(self, name):
        action = QAction(name, self)
        action.setCheckable(True)
        self._theme_menu.addAction(action)
        self._theme_group.addAction(action)
        self._user_theme_actions.append(action)
        return action

    def clear_user_theme_actions(self):
        for action in self._user_theme_actions:
            self._theme_menu.removeAction(action)
            self._theme_group.removeAction(action)
            action.deleteLater()
        self._user_theme_actions.clear()

    def set_active_theme(self, name):
        self.registry["theme.light"].setChecked(name == "light")
        self.registry["theme.dark"].setChecked(name == "dark")
        for action in self._user_theme_actions:
            action.setChecked(action.text() == name)
