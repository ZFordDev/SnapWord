"""Document lifecycle, tab state, and file dialogs."""

from pathlib import Path

from PySide6.QtCore import QObject, QSignalBlocker, QStandardPaths
from PySide6.QtGui import QTextCursor, QTextDocument
from PySide6.QtWidgets import QFileDialog, QMessageBox

from ..formats import SUPPORTED_OPEN_FILTER, SUPPORTED_SAVE_FILTER, load_as_html, save_document
from .conversion import confirm_conversion
from .tabs import TabDocument


class DocumentController(QObject):
    def __init__(self, window, editor, tabs):
        super().__init__(window)
        self.window, self.editor, self.bar = window, editor, tabs
        self.tabs = []
        self.active = -1
        self._loading = False
        tabs.tab_changed.connect(self.activate)
        tabs.tab_close_requested.connect(self.close_tab)
        tabs.tab_moved.connect(self.move_tab)
        tabs.new_tab_requested.connect(self.new)
        editor.file_dirty_changed.connect(self.dirty_changed)

    def new(self):
        self.tabs.append(TabDocument())
        with QSignalBlocker(self.bar):
            index = self.bar.add_tab("Untitled")
        self.bar.set_current_index(index)
        self.activate(index)

    def snapshot(self):
        if not 0 <= self.active < len(self.tabs):
            return
        doc = self.tabs[self.active]
        doc.html = self.editor.toHtml()
        cursor = self.editor.textCursor()
        doc.cursor_block, doc.cursor_col = cursor.blockNumber(), cursor.columnNumber()
        doc.path, doc.dirty = self.editor.current_path(), self.editor.is_dirty()
        doc.scroll = self.window.page_scroll_area.verticalScrollBar().value()

    def activate(self, index):
        if self._loading or index == self.active or not 0 <= index < len(self.tabs):
            return
        self.snapshot()
        self.active = index
        self._loading = True
        try:
            doc = self.tabs[index]
            fresh = doc.document is None
            if fresh:
                doc.document = QTextDocument(self)
                doc.document.setDefaultFont(self.editor.document().defaultFont())
                doc.document.setHtml(doc.html)
                doc.document.setUndoRedoEnabled(True)
                doc.document.setModified(False)
            self.editor.attach_document(doc.document, doc.path)
            if fresh and not doc.html:
                self.editor.set_line_spacing(self.editor.default_line_spacing)
                doc.document.clearUndoRedoStacks()
                doc.document.setModified(False)
            cursor = self.editor.textCursor()
            block = self.editor.document().findBlockByNumber(doc.cursor_block)
            cursor.setPosition(block.position() if block.isValid() else 0)
            cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, doc.cursor_col)
            self.editor.setTextCursor(cursor)
            self.window.page_scroll_area.restore_scroll(doc.scroll)
            self.refresh(index)
        finally:
            self._loading = False

    def refresh(self, index):
        doc = self.tabs[index]
        self.bar.set_tab_label(index, doc.label)
        self.bar.set_tab_dirty(index, doc.dirty)
        if index == self.active:
            title = f"{doc.label} — SnapWord"
            self.window.setWindowTitle(title + (" •" if doc.dirty else ""))

    def dirty_changed(self, dirty):
        if self._loading or self.active < 0:
            return
        self.tabs[self.active].dirty = dirty
        self.refresh(self.active)

    def move_tab(self, source, target):
        active_doc = self.tabs[self.active]
        doc = self.tabs.pop(source)
        self.tabs.insert(target, doc)
        self.active = next(i for i, candidate in enumerate(self.tabs) if candidate is active_doc)

    @staticmethod
    def documents_path():
        return QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)

    def open_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self.window, "Open Document", self.documents_path(), SUPPORTED_OPEN_FILTER
        )
        if path:
            self.load_file(path)

    def open_folder(self):
        path = QFileDialog.getExistingDirectory(self.window, "Open Folder", self.documents_path())
        if path:
            self.window.file_tree.set_root_path(path)
            self.window.file_tree_dock.show()

    def load_file(self, path):
        path = str(Path(path).resolve())
        for index, doc in enumerate(self.tabs):
            if doc.path and Path(doc.path).resolve() == Path(path):
                self.bar.set_current_index(index)
                return
        try:
            if not confirm_conversion(self.window, path, importing=True):
                return
            html = load_as_html(path)
        except Exception as exc:
            QMessageBox.warning(self.window, "Open failed", str(exc))
            return
        self.tabs.append(TabDocument(path=path, html=html, label=Path(path).name))
        with QSignalBlocker(self.bar):
            index = self.bar.add_tab(Path(path).name)
        self.bar.set_current_index(index)
        self.activate(index)
        self.window.file_tree.set_root_path(str(Path(path).parent))

    def save(self):
        return self.save_tab(self.active)

    def save_as(self):
        return self.save_tab(self.active, save_as=True)

    def save_tab(self, index, save_as=False):
        if not 0 <= index < len(self.tabs):
            return False
        self.snapshot()
        doc = self.tabs[index]
        path = doc.path
        if save_as or not path:
            path, selected = QFileDialog.getSaveFileName(
                self.window, "Save Document", path or self.documents_path(), SUPPORTED_SAVE_FILTER
            )
            if not path:
                return False
            path = self.add_selected_suffix(path, selected)
        if not confirm_conversion(self.window, path):
            return False
        try:
            # Saving an inactive tab must never copy the active editor over it.
            from PySide6.QtGui import QTextDocument

            document = QTextDocument()
            document.setHtml(doc.html)
            save_document(path, doc.html, document.toPlainText())
        except Exception as exc:
            QMessageBox.warning(self.window, "Save failed", str(exc))
            return False
        doc.path, doc.label, doc.dirty = path, Path(path).name, False
        if doc.document is not None:
            doc.document.setModified(False)
        if index == self.active:
            self.editor.mark_saved(path)
        self.refresh(index)
        return True

    @staticmethod
    def ensure_suffix(path, suffix):
        return path if Path(path).suffix else path + suffix

    @classmethod
    def add_selected_suffix(cls, path, selected):
        suffixes = {
            "SnapWord Documents": ".docs",
            "Microsoft Word": ".docx",
            "OpenDocument Text": ".odt",
            "Rich Text Format": ".rtf",
            "Plain Text": ".txt",
            "HTML": ".html",
            "Markdown": ".md",
        }
        for label, suffix in suffixes.items():
            if selected.startswith(label):
                return cls.ensure_suffix(path, suffix)
        return path

    def export(self, suffix):
        path, _ = QFileDialog.getSaveFileName(
            self.window,
            f"Export as {suffix[1:].upper()}",
            str(Path(self.documents_path()) / f"{Path(self.editor.current_path() or 'Untitled').stem}{suffix}"),
            f"{suffix[1:].upper()} Files (*{suffix});;All Files (*)",
        )
        if path:
            self.editor.export_document(self.ensure_suffix(path, suffix))

    def close_tab(self, index):
        if not 0 <= index < len(self.tabs):
            return
        self.snapshot()
        doc = self.tabs[index]
        if doc.dirty:
            reply = QMessageBox.question(
                self.window,
                "Unsaved Changes",
                f'Save "{doc.label}" before closing?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )
            if reply == QMessageBox.Cancel or (reply == QMessageBox.Save and not self.save_tab(index)):
                return
        active_doc = self.tabs[self.active]
        self.tabs.pop(index)
        with QSignalBlocker(self.bar):
            self.bar.remove_tab(index)
        if not self.tabs:
            self.active = -1
            self.new()
        elif active_doc is doc:
            self.active = -1
            target = min(index, len(self.tabs) - 1)
            self.bar.set_current_index(target)
            self.activate(target)
        else:
            self.active = next(i for i, candidate in enumerate(self.tabs) if candidate is active_doc)
            self.bar.set_current_index(self.active)
            self.refresh(self.active)

    def confirm_close(self):
        self.snapshot()
        dirty = [i for i, doc in enumerate(self.tabs) if doc.dirty]
        if not dirty:
            return True
        reply = QMessageBox.question(
            self.window,
            "Unsaved Changes",
            f"Save {len(dirty)} document(s) before closing?",
            QMessageBox.SaveAll | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.SaveAll,
        )
        if reply == QMessageBox.Discard:
            return True
        if reply == QMessageBox.SaveAll:
            return all(self.save_tab(index) for index in dirty)
        return False
