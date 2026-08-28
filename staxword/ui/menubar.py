from __future__ import annotations

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMenuBar, QWidget


class StaxWordMenuBar(QMenuBar):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        action_parent = parent if parent is not None else self

        # --- File Menu ---
        file_menu = self.addMenu("File")
        self.action_open = QAction("Open", action_parent)
        self.action_save = QAction("Save", action_parent)
        self.action_save_as = QAction("Save As", action_parent)

        self.action_open.setShortcut(QKeySequence.StandardKey.Open)
        self.action_save.setShortcut(QKeySequence.StandardKey.Save)
        self.action_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))

        file_menu.addAction(self.action_open)
        file_menu.addAction(self.action_save)
        file_menu.addAction(self.action_save_as)

        file_menu.addSeparator()

        self.action_print = QAction("Print", action_parent)
        self.action_print.setShortcut(QKeySequence.StandardKey.Print)
        file_menu.addAction(self.action_print)

        self.action_export_pdf = QAction("Export as PDF", action_parent)
        self.action_export_pdf.setShortcut(QKeySequence("Ctrl+Shift+P"))
        file_menu.addAction(self.action_export_pdf)

        # --- Edit Menu ---
        edit_menu = self.addMenu("Edit")
        self.action_find = QAction("Find & Replace", action_parent)
        self.action_find.setShortcut(QKeySequence("Ctrl+H"))
        edit_menu.addAction(self.action_find)

        self.action_find_simple = QAction("Find", action_parent)
        self.action_find_simple.setShortcut(QKeySequence("Ctrl+F"))
        edit_menu.addAction(self.action_find_simple)

        edit_menu.addSeparator()

        self.action_preferences = QAction("Preferences...", action_parent)
        self.action_preferences.setShortcut(QKeySequence("Ctrl+,"))
        edit_menu.addAction(self.action_preferences)

        # --- View Menu ---
        view_menu = self.addMenu("View")
        self.action_view_filetree = QAction("Show File Tree", action_parent)
        self.action_view_filetree.setCheckable(True)
        self.action_view_filetree.setChecked(False)
        self.action_view_filetree.setShortcut(QKeySequence("Ctrl+Shift+F"))
        view_menu.addAction(self.action_view_filetree)

        # --- Theme Menu ---
        theme_menu = self.addMenu("Theme")
        self.action_theme_light = QAction("Light", action_parent)
        self.action_theme_light.setCheckable(True)
        self.action_theme_light.setChecked(True)
        self.action_theme_dark = QAction("Dark", action_parent)
        self.action_theme_dark.setCheckable(True)
        self.action_theme_edit = QAction("Edit Themes...", action_parent)

        theme_menu.addAction(self.action_theme_light)
        theme_menu.addAction(self.action_theme_dark)
        theme_menu.addSeparator()
        theme_menu.addAction(self.action_theme_edit)

        self._theme_menu = theme_menu
        self._user_theme_actions: list[QAction] = []

    def add_user_theme_action(self, name: str) -> QAction:
        action = QAction(name, self.parent())
        action.setCheckable(True)
        self._theme_menu.addAction(action)
        self._user_theme_actions.append(action)
        return action

    def clear_user_theme_actions(self) -> None:
        for action in self._user_theme_actions:
            self._theme_menu.removeAction(action)
        self._user_theme_actions.clear()

    def set_active_theme(self, name: str) -> None:
        self.action_theme_light.setChecked(name == "light")
        self.action_theme_dark.setChecked(name == "dark")
        for action in self._user_theme_actions:
            action.setChecked(action.text() == name)
