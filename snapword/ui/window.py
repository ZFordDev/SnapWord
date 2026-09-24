"""Application composition; document, toolbar and workspace behavior live separately."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from ..branding import application_icon
from ..fonts import make_font
from ..themes import apply_theme_to_widget, list_themes
from .actions import ActionRegistry
from .documents import DocumentController
from .editor import SnapWordEditor
from .findbar import FindReplaceBar
from .footer import SnapWordFooter
from .layout_state import WorkspaceLayout
from .menubar import SnapWordMenuBar
from .panels import FilesDock
from .preferences import PreferencesDialog, load_prefs
from .tabs import SnapWordTabBar
from .themeditor import ThemeEditorDialog
from .toolbar import ToolbarManager
from .workspace import DocumentWorkspace


class SnapWordWindow(QMainWindow):
    def __init__(self, version="0.1.0", *, settings=None):
        super().__init__()
        self.setWindowIcon(application_icon())
        self.setWindowTitle("SnapWord")
        self.resize(1200, 900)
        self.editor = SnapWordEditor()
        self.tab_bar = SnapWordTabBar()
        self.find_bar = FindReplaceBar(self.editor)
        self.find_bar.hide()
        self.find_bar.close_requested.connect(self._close_find_bar)
        self.page_scroll_area = DocumentWorkspace(self.editor)
        self._page_container = self.page_scroll_area.page
        self.footer = SnapWordFooter(version)
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        for widget in (self.tab_bar, self.find_bar):
            layout.addWidget(widget)
        layout.addWidget(self.page_scroll_area, 1)
        layout.addWidget(self.footer)
        self.setCentralWidget(root)

        self.file_tree_dock = FilesDock(self)
        self.file_tree = self.file_tree_dock.tree
        self.addDockWidget(Qt.LeftDockWidgetArea, self.file_tree_dock)
        self.documents = DocumentController(self, self.editor, self.tab_bar)
        self.actions = ActionRegistry(self)
        self.toolbar = ToolbarManager(self, self.editor, self.actions)
        self.toolbar_sections = self.toolbar.sections
        self._register_commands()
        self.menu_bar = SnapWordMenuBar(self.actions, self)
        self.setMenuBar(self.menu_bar)
        for bar in self.toolbar_sections.values():
            self.menu_bar.toolbar_menu.addAction(bar.toggleViewAction())
        files_action = self.file_tree_dock.toggleViewAction()
        files_action.setShortcut("Ctrl+Shift+F")
        self.menu_bar.view_menu.insertAction(self.actions["view.reset"], files_action)
        self.menu_bar.action_view_filetree = files_action
        self.file_tree.file_opened.connect(self.load_file)
        self.editor.metrics_changed.connect(self.footer.update_metrics)
        self.editor.cursorPositionChanged.connect(self._on_cursor_position_changed)

        # Capture and restore only after every named toolbar and dock exists.
        self.workspace_layout = WorkspaceLayout(self, self.toolbar, self.file_tree_dock, settings)
        self._refresh_theme_menu()
        self.apply_theme(self.workspace_layout.settings.value("theme", "light"))
        self._apply_prefs(load_prefs())
        self.documents.new()
        self.workspace_layout.restore()

    def _register_commands(self):
        commands = (
            ("file.new", "New document", self.documents.new, "Ctrl+N"),
            ("file.open", "Open File…", self.documents.open_dialog, "Ctrl+O"),
            ("file.folder", "Open Folder…", self.documents.open_folder, None),
            ("file.save", "Save", self.documents.save, "Ctrl+S"),
            ("file.save_as", "Save As…", self.documents.save_as, "Ctrl+Shift+S"),
            ("edit.find", "Find", self._open_find, "Ctrl+F"),
            ("edit.replace", "Find & Replace", self._open_find_replace, "Ctrl+H"),
            ("edit.preferences", "Preferences…", self._open_preferences, "Ctrl+,"),
            ("view.reset", "Reset Workspace Layout", self._reset_workspace_layout, None),
            ("theme.edit", "Edit Themes…", self._open_theme_editor, None),
        )
        for key, label, callback, shortcut in commands:
            self.actions.add(key, label, callback, shortcut=shortcut)
        for extension in ("rtf", "txt", "html", "md"):
            self.actions.add(
                f"file.{extension}",
                f"Export as {extension.upper()}",
                lambda checked=False, ext=extension: self.documents.export("." + ext),
            )
        for name in ("light", "dark"):
            self.actions.add(
                f"theme.{name}", name.title(), lambda checked=False, theme=name: self.apply_theme(theme), checkable=True
            )

    def _reset_workspace_layout(self):
        self.workspace_layout.reset()

    def _toggle_file_tree(self):
        self.file_tree_dock.setVisible(self.file_tree_dock.isHidden())

    def _open_find(self):
        self.find_bar.replace_widget.hide()
        self.find_bar.show()
        self.find_bar.focus_search()

    def _open_find_replace(self):
        self.find_bar.show_replace()
        self.find_bar.focus_search()

    def _close_find_bar(self):
        self.find_bar.hide()
        self.editor.setFocus()

    def apply_theme(self, theme_name):
        apply_theme_to_widget(self, theme_name)
        self._current_theme = theme_name
        self.menu_bar.set_active_theme(theme_name)

    def _refresh_theme_menu(self):
        self.menu_bar.clear_user_theme_actions()
        for name, info in sorted(list_themes().items()):
            if not info["builtin"]:
                action = self.menu_bar.add_user_theme_action(name)
                action.triggered.connect(lambda checked=False, theme=name: self.apply_theme(theme))

    def _open_theme_editor(self):
        dialog = ThemeEditorDialog(self)
        dialog.theme_saved.connect(self._on_theme_saved)
        dialog.exec()

    def _on_theme_saved(self, name):
        self._refresh_theme_menu()
        self.apply_theme(name)

    def _open_preferences(self):
        dialog = PreferencesDialog(self)
        dialog.prefs_changed.connect(self._apply_prefs)
        dialog.exec()

    def _apply_prefs(self, prefs):
        size = self._valid_size(prefs.get("editor_font_size"), 12)
        font = make_font([str(prefs.get("editor_font_family", "Arial"))], size)
        self.editor.setFont(font)
        self.editor.document().setDefaultFont(font)
        try:
            spacing = float(prefs.get("line_spacing", 1.5))
            self.editor.default_line_spacing = spacing if 0.5 <= spacing <= 4 else 1.5
        except (TypeError, ValueError):
            self.editor.default_line_spacing = 1.5
        self.toolbar.set_font_size(self._valid_size(prefs.get("toolbar_font_size"), 13))
        sidebar_size = self._valid_size(prefs.get("sidebar_font_size"), 13)
        footer_size = self._valid_size(prefs.get("footer_font_size"), 11)
        self.file_tree.setStyleSheet(f"QTreeView {{ font-size: {sidebar_size}px; }}")
        self.footer.setStyleSheet(f"QLabel {{ font-size: {footer_size}px; }}")

    @staticmethod
    def _valid_size(value, default):
        try:
            return max(1, min(512, int(value)))
        except (TypeError, ValueError, OverflowError):
            return default

    def _on_cursor_position_changed(self):
        cursor = self.editor.textCursor()
        self.footer.update_cursor_position(cursor.blockNumber() + 1, cursor.columnNumber() + 1)

    def load_file(self, path):
        self.documents.load_file(path)

    def _new_tab(self):
        self.documents.new()

    @property
    def _tabs(self):
        return self.documents.tabs

    @property
    def _active_tab(self):
        return self.documents.active

    def closeEvent(self, event):
        if self.documents.confirm_close():
            self.workspace_layout.save()
            event.accept()
        else:
            event.ignore()
