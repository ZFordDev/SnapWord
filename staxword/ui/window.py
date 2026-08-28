from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..themes import apply_theme_to_widget, list_themes
from .editor import StaxWordEditor
from .filetree import StaxWordFileTree
from .findbar import FindReplaceBar
from .footer import StaxWordFooter
from .menubar import StaxWordMenuBar
from .preferences import PreferencesDialog, load_prefs
from .tabs import StaxWordTabBar, TabDocument
from .themeditor import ThemeEditorDialog
from .toolbar import StaxWordToolbar


class StaxWordWindow(QWidget):
    def __init__(self, version: str = "0.1.0") -> None:
        super().__init__()
        self.setWindowTitle("StaxWord - Word Editor")
        self.resize(1200, 900)

        # --- Tab state ---
        self._tabs: list[TabDocument] = []
        self._active_tab: int = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Menu bar
        self.menu_bar = StaxWordMenuBar()
        layout.addWidget(self.menu_bar)

        # Formatting toolbar
        self.editor = StaxWordEditor()
        self.toolbar = StaxWordToolbar(self.editor)
        layout.addWidget(self.toolbar)

        # Find & Replace bar (hidden by default)
        self.find_bar = FindReplaceBar(self.editor)
        self.find_bar.hide()
        self.find_bar.close_requested.connect(self._close_find_bar)
        layout.addWidget(self.find_bar)

        # Tab bar
        self.tab_bar = StaxWordTabBar()
        layout.addWidget(self.tab_bar)

        # Main splitter: file tree + centered page workspace
        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setObjectName("AppContainer")
        self._splitter.setHandleWidth(1)
        self._splitter.setChildrenCollapsible(False)

        self.file_tree = StaxWordFileTree()
        self._splitter.addWidget(self.file_tree)

        # Centered page workspace (gray background, white page)
        workspace = QWidget()
        workspace.setObjectName("PageWorkspace")
        workspace_layout = QHBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)
        workspace_layout.addStretch(1)

        # White page container (percentage-based width)
        self._page_container = QWidget()
        self._page_container.setObjectName("PageContainer")
        self._page_container.setMinimumWidth(500)
        page_layout = QVBoxLayout(self._page_container)
        page_layout.setContentsMargins(0, 24, 0, 24)
        page_layout.setSpacing(0)
        page_layout.addWidget(self.editor)

        workspace_layout.addWidget(self._page_container, 3)
        workspace_layout.addStretch(1)

        self._splitter.addWidget(workspace)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)

        layout.addWidget(self._splitter, 1)

        # Footer
        self.footer = StaxWordFooter(version)
        layout.addWidget(self.footer)

        # Default: file tree hidden (word editor is document-centric)
        self.file_tree.hide()

        # Default theme
        self._current_theme = "light"
        self.apply_theme("light")
        self._refresh_theme_menu()

        # Apply user prefs
        prefs = load_prefs()
        self._apply_prefs(prefs)

        # Wire signals
        self.editor.metrics_changed.connect(self.footer.update_metrics)
        self.editor.file_dirty_changed.connect(self._on_editor_dirty_changed)
        self.editor.cursorPositionChanged.connect(self._on_cursor_position_changed)
        self.file_tree.file_opened.connect(self.load_file)

        # --- Wire menu actions ---
        self.menu_bar.action_open.triggered.connect(self._on_open)
        self.menu_bar.action_save.triggered.connect(self._on_save)
        self.menu_bar.action_save_as.triggered.connect(self._on_save_as)
        self.menu_bar.action_theme_light.triggered.connect(lambda: self.apply_theme("light"))
        self.menu_bar.action_theme_dark.triggered.connect(lambda: self.apply_theme("dark"))
        self.menu_bar.action_theme_edit.triggered.connect(self._open_theme_editor)
        self.menu_bar.action_view_filetree.triggered.connect(self._toggle_file_tree)
        self.menu_bar.action_find.triggered.connect(self._open_find_replace)
        self.menu_bar.action_find_simple.triggered.connect(self._open_find)
        self.menu_bar.action_print.triggered.connect(self.editor.print_document)
        self.menu_bar.action_export_pdf.triggered.connect(self.editor.export_pdf)
        self.menu_bar.action_preferences.triggered.connect(self._open_preferences)

        # --- Wire tab bar ---
        self.tab_bar.tab_changed.connect(self._on_tab_changed)
        self.tab_bar.tab_close_requested.connect(self._on_tab_close_requested)
        self.tab_bar.new_tab_requested.connect(self._new_tab)

        # Create first tab
        self._new_tab()
        self.set_view_mode("split")

    # ---------------------------------------------------------
    # Tab management
    # ---------------------------------------------------------

    def _new_tab(self) -> None:
        doc = TabDocument()
        self._tabs.append(doc)
        idx = self.tab_bar.add_tab(doc.label)
        self.tab_bar.set_current_index(idx)

    def _on_tab_changed(self, idx: int) -> None:
        if idx == self._active_tab:
            return
        if idx < 0 or idx >= len(self._tabs):
            return
        self._save_tab_state(self._active_tab)
        self._active_tab = idx
        self._load_tab_state(idx)
        self._update_title_dirty(self._tabs[idx].dirty)

    def _on_tab_close_requested(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._tabs):
            return
        doc = self._tabs[idx]
        if doc.dirty:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                f'"{doc.label}" has unsaved changes. Save before closing?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )
            if reply == QMessageBox.Save:
                if doc.path:
                    self._save_tab_state(idx)
                    old_active = self._active_tab
                    self._active_tab = idx
                    self._load_tab_state(idx)
                    self.editor.save_file()
                    doc.dirty = False
                    self._active_tab = old_active
                    if old_active >= 0:
                        self._load_tab_state(old_active)
                else:
                    return
            elif reply == QMessageBox.Cancel:
                return

        self.tab_bar.remove_tab(idx)
        self._tabs.pop(idx)

        if not self._tabs:
            self._new_tab()
            return

        if self._active_tab >= len(self._tabs):
            self._active_tab = len(self._tabs) - 1
        elif self._active_tab > idx:
            self._active_tab -= 1

        self.tab_bar.set_current_index(self._active_tab)
        self._load_tab_state(self._active_tab)
        self._update_title_dirty(self._tabs[self._active_tab].dirty)

    def _save_tab_state(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._tabs):
            return
        doc = self._tabs[idx]
        doc.html = self.editor.toHtml()
        cursor = self.editor.textCursor()
        doc.cursor_block = cursor.blockNumber()
        doc.cursor_col = cursor.columnNumber()
        doc.path = self.editor.current_path()
        doc.dirty = self.editor.is_dirty()
        if doc.path:
            doc.label = Path(doc.path).name

    def _load_tab_state(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._tabs):
            return
        doc = self._tabs[idx]

        # Disconnect to avoid re-triggering during load
        self.editor.file_dirty_changed.disconnect(self._on_editor_dirty_changed)
        if doc.html:
            self.editor.setHtml(doc.html)
        else:
            self.editor.setPlainText("")
        self.editor.file_dirty_changed.connect(self._on_editor_dirty_changed)

        # Restore cursor
        from PySide6.QtGui import QTextCursor

        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        for _ in range(doc.cursor_block):
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
        cursor.movePosition(
            QTextCursor.MoveOperation.Right,
            QTextCursor.MoveMode.MoveAnchor,
            doc.cursor_col,
        )
        self.editor.setTextCursor(cursor)

        # Restore path and dirty state
        self.editor._current_path = doc.path
        self.editor._dirty = doc.dirty
        self.editor.file_dirty_changed.emit(doc.dirty)

        # Update tab label and dirty indicator
        self.tab_bar.set_tab_label(idx, doc.label)
        self.tab_bar.set_tab_dirty(idx, doc.dirty)

    def _on_editor_dirty_changed(self, dirty: bool) -> None:
        if 0 <= self._active_tab < len(self._tabs):
            self._tabs[self._active_tab].dirty = dirty
            self.tab_bar.set_tab_dirty(self._active_tab, dirty)
        self._update_title_dirty(dirty)

    # ---------------------------------------------------------
    # View menu
    # ---------------------------------------------------------

    def _toggle_file_tree(self) -> None:
        if self.file_tree.isVisible():
            self.file_tree.hide()
            self.menu_bar.action_view_filetree.setChecked(False)
        else:
            self.file_tree.show()
            self.menu_bar.action_view_filetree.setChecked(True)

    def _open_find_replace(self) -> None:
        self.find_bar.show_replace()
        self.find_bar.focus_search()

    def _open_find(self) -> None:
        self.find_bar.show()
        self.find_bar.focus_search()

    def _close_find_bar(self) -> None:
        self.find_bar.hide()
        self.editor.setFocus()

    def set_view_mode(self, mode: str) -> None:
        """Stub for future view modes (page view, draft, etc.)."""
        pass

    # ---------------------------------------------------------
    # File operations
    # ---------------------------------------------------------

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Document", "",
            "StaxWord Files (*.staxdoc);;HTML Files (*.html *.htm);;All Files (*)",
        )
        if path:
            self.load_file(path)

    def _on_save(self) -> None:
        if self._active_tab < 0:
            return
        doc = self._tabs[self._active_tab]
        if doc.path:
            self.editor.save_file()
            doc.dirty = False
            self.tab_bar.set_tab_dirty(self._active_tab, False)
            self._update_title_dirty(False)
        else:
            self._on_save_as()

    def _on_save_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Document", "",
            "StaxWord Files (*.staxdoc);;HTML Files (*.html);;All Files (*)",
        )
        if path:
            self.editor.save_file(path)
            if self._active_tab >= 0:
                doc = self._tabs[self._active_tab]
                doc.path = path
                doc.label = Path(path).name
                doc.dirty = False
                self.tab_bar.set_tab_label(self._active_tab, doc.label)
                self.tab_bar.set_tab_dirty(self._active_tab, False)
            self._update_title_dirty(False)

    # ---------------------------------------------------------
    # Theme
    # ---------------------------------------------------------

    def apply_theme(self, theme_name: str) -> None:
        apply_theme_to_widget(self, theme_name)
        self._current_theme = theme_name
        self.menu_bar.set_active_theme(theme_name)

    def _refresh_theme_menu(self) -> None:
        self.menu_bar.clear_user_theme_actions()
        themes = list_themes()
        for name, info in sorted(themes.items()):
            if not info["builtin"]:
                action = self.menu_bar.add_user_theme_action(name)
                action.triggered.connect(lambda checked, n=name: self.apply_theme(n))

    def _open_theme_editor(self, initial_name: str = "", initial_colors: dict | None = None) -> None:
        dialog = ThemeEditorDialog(self, initial_name=initial_name, initial_colors=initial_colors)
        dialog.theme_saved.connect(self._on_theme_saved)
        dialog.exec()

    def _on_theme_saved(self, theme_name: str) -> None:
        self._refresh_theme_menu()
        self.apply_theme(theme_name)

    def _open_preferences(self) -> None:
        dialog = PreferencesDialog(self)
        dialog.prefs_changed.connect(self._apply_prefs)
        dialog.exec()

    def _apply_prefs(self, prefs: dict) -> None:
        """Apply user preferences to the editor and UI."""
        from PySide6.QtGui import QFont

        font_family = prefs.get("editor_font_family", "Arial")
        font_size = prefs.get("editor_font_size", 12)
        self.editor.setFont(QFont(font_family, font_size))

        spacing = prefs.get("line_spacing", 1.5)
        self.editor.set_line_spacing(spacing)

        # Update toolbar font size via stylesheet
        tb_size = prefs.get("toolbar_font_size", 13)
        self.toolbar.setStyleSheet(f"QToolBar QToolButton {{ font-size: {tb_size}px; }}")

    # ---------------------------------------------------------
    # Title / dirty state
    # ---------------------------------------------------------

    def _update_title_dirty(self, dirty: bool) -> None:
        title = "StaxWord - Word Editor"
        if 0 <= self._active_tab < len(self._tabs):
            doc = self._tabs[self._active_tab]
            if doc.path:
                title += f" \u2014 {doc.path}"
        if dirty:
            title += " \u2022"
        self.setWindowTitle(title)

    # ---------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------

    def load_file(self, path: str) -> None:
        # Check if file is already open in a tab
        for idx, doc in enumerate(self._tabs):
            if doc.path == path:
                self.tab_bar.set_current_index(idx)
                return

        doc = TabDocument.from_path(path)
        idx = self.tab_bar.add_tab(doc.label)
        self._tabs.append(doc)
        self.tab_bar.set_current_index(idx)

    # ---------------------------------------------------------
    # Footer cursor
    # ---------------------------------------------------------

    def _on_cursor_position_changed(self) -> None:
        cursor = self.editor.textCursor()
        self.footer.update_cursor_position(cursor.blockNumber() + 1, cursor.columnNumber() + 1)

    # ---------------------------------------------------------
    # Close confirmation
    # ---------------------------------------------------------

    def closeEvent(self, event) -> None:
        self._save_tab_state(self._active_tab)

        dirty_tabs = [doc for doc in self._tabs if doc.dirty]
        if not dirty_tabs:
            event.accept()
            return

        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            f"{len(dirty_tabs)} document(s) have unsaved changes. Save before closing?",
            QMessageBox.SaveAll | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.SaveAll,
        )

        if reply == QMessageBox.SaveAll:
            for idx, doc in enumerate(self._tabs):
                if doc.dirty and doc.path:
                    self._active_tab = idx
                    self._load_tab_state(idx)
                    self.editor.save_file()
                    doc.dirty = False
            event.accept()
        elif reply == QMessageBox.Discard:
            event.accept()
        else:
            event.ignore()
