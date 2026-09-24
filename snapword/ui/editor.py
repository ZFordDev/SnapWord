from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextBlockFormat, QTextCharFormat, QTextListFormat
from PySide6.QtWidgets import QAbstractScrollArea, QSizePolicy, QTextEdit

from snapword.fonts import UI_TEXT, make_font
from snapword.formats import load_as_html, save_document
from snapword.images import image_data_url, portable_html
from snapword.storage import atomic_destination

from .conversion import confirm_conversion
from .metrics import PAGE_VERTICAL_PADDING


class SnapWordEditor(QTextEdit):
    _PAGE_VERTICAL_PADDING = PAGE_VERTICAL_PADDING * 2

    metrics_changed = Signal(int, int)  # words, chars
    file_dirty_changed = Signal(bool)
    cursor_format_changed = Signal()  # emitted when cursor position/selection changes

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("RichTextEdit")
        self.setFont(make_font(UI_TEXT, 12))
        self.setPlaceholderText("Start typing your document here...")
        self.setAcceptRichText(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustIgnored)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._current_path: str | None = None
        self._dirty: bool = False
        self.default_line_spacing = 1.5

        self.textChanged.connect(self._on_text_changed)
        self.cursorPositionChanged.connect(self._on_cursor_moved)
        self.currentCharFormatChanged.connect(lambda _format: self.cursor_format_changed.emit())
        self.textChanged.connect(self.cursor_format_changed.emit)
        self.document().documentLayout().documentSizeChanged.connect(self._update_document_height)
        self.document().modificationChanged.connect(self._modification_changed)
        self._update_document_height()

    def _modification_changed(self, dirty):
        if dirty != self._dirty:
            self._dirty = dirty
            self.file_dirty_changed.emit(dirty)

    def setPlainText(self, text):
        """Treat explicit content replacement as an edit, not a file load."""
        super().setPlainText(text)
        self.document().setModified(True)

    def attach_document(self, document, path):
        previous = self.document()
        if previous is not document:
            previous.documentLayout().documentSizeChanged.disconnect(self._update_document_height)
            previous.modificationChanged.disconnect(self._modification_changed)
            self.setDocument(document)
            document.documentLayout().documentSizeChanged.connect(self._update_document_height)
            document.modificationChanged.connect(self._modification_changed)
        self._current_path = path
        self._modification_changed(document.isModified())
        self._update_document_height()
        self.cursor_format_changed.emit()
        self.undoAvailable.emit(document.isUndoAvailable())
        self.redoAvailable.emit(document.isRedoAvailable())

    def _update_document_height(self) -> None:
        document_height = self.document().documentLayout().documentSize().height()
        self.setFixedHeight(max(1, round(document_height) + self._PAGE_VERTICAL_PADDING))

    # ---------------------------------------------------------
    # Formatting helpers
    # ---------------------------------------------------------

    def _toggle_char_format(self, fmt: QTextCharFormat) -> None:
        cursor = self.textCursor()
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        else:
            self.mergeCurrentCharFormat(fmt)

    def set_bold(self, on: bool = True) -> None:
        fmt = QTextCharFormat()
        fmt.setFontWeight(700 if on else 400)
        self._toggle_char_format(fmt)

    def set_italic(self, on: bool = True) -> None:
        fmt = QTextCharFormat()
        fmt.setFontItalic(on)
        self._toggle_char_format(fmt)

    def set_underline(self, on: bool = True) -> None:
        fmt = QTextCharFormat()
        fmt.setFontUnderline(on)
        self._toggle_char_format(fmt)

    def set_strikethrough(self, on: bool = True) -> None:
        fmt = QTextCharFormat()
        fmt.setFontStrikeOut(on)
        self._toggle_char_format(fmt)

    def set_superscript(self, on: bool = True) -> None:
        fmt = QTextCharFormat()
        fmt.setVerticalAlignment(
            QTextCharFormat.VerticalAlignment.AlignSuperScript
            if on
            else QTextCharFormat.VerticalAlignment.AlignNormal
        )
        self._toggle_char_format(fmt)

    def set_subscript(self, on: bool = True) -> None:
        fmt = QTextCharFormat()
        fmt.setVerticalAlignment(
            QTextCharFormat.VerticalAlignment.AlignSubScript
            if on
            else QTextCharFormat.VerticalAlignment.AlignNormal
        )
        self._toggle_char_format(fmt)

    def set_font_family(self, family: str) -> None:
        fmt = QTextCharFormat()
        fmt.setFontFamilies([family])
        self._toggle_char_format(fmt)

    def set_font_size(self, size: float) -> None:
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        self._toggle_char_format(fmt)

    def set_text_color(self, color) -> None:
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        self._toggle_char_format(fmt)

    def set_highlight_color(self, color) -> None:
        fmt = QTextCharFormat()
        fmt.setBackground(color)
        self._toggle_char_format(fmt)

    def clear_formatting(self) -> None:
        cursor = self.textCursor()
        if cursor.hasSelection():
            fmt = QTextCharFormat()
            cursor.setCharFormat(fmt)
        else:
            fmt = QTextCharFormat()
            self.setCurrentCharFormat(fmt)

    def set_heading(self, level: int) -> None:
        block_fmt = QTextBlockFormat()
        if level == 0:
            block_fmt.setHeadingLevel(0)
            char_fmt = QTextCharFormat()
            char_fmt.setFontPointSize(12)
            char_fmt.setFontWeight(400)
        else:
            block_fmt.setHeadingLevel(level)
            sizes = {1: 24, 2: 18, 3: 14}
            char_fmt = QTextCharFormat()
            char_fmt.setFontPointSize(sizes.get(level, 12))
            char_fmt.setFontWeight(700)

        cursor = self.textCursor()
        cursor.mergeBlockFormat(block_fmt)
        cursor.mergeCharFormat(char_fmt)
        self.setTextCursor(cursor)

    def set_bullet_list(self) -> None:
        cursor = self.textCursor()
        list_fmt = QTextListFormat()
        list_fmt.setStyle(QTextListFormat.Style.ListDisc)
        cursor.createList(list_fmt)

    def set_numbered_list(self) -> None:
        cursor = self.textCursor()
        list_fmt = QTextListFormat()
        list_fmt.setStyle(QTextListFormat.Style.ListDecimal)
        cursor.createList(list_fmt)

    def set_alignment(self, alignment) -> None:
        self.setAlignment(alignment)

    def set_justify(self) -> None:
        self.setAlignment(Qt.AlignJustify)

    def set_indent(self) -> None:
        cursor = self.textCursor()
        block_fmt = cursor.blockFormat()
        block_fmt.setIndent(block_fmt.indent() + 1)
        cursor.setBlockFormat(block_fmt)
        self.setTextCursor(cursor)

    def set_outdent(self) -> None:
        cursor = self.textCursor()
        block_fmt = cursor.blockFormat()
        indent = block_fmt.indent()
        if indent > 0:
            block_fmt.setIndent(indent - 1)
            cursor.setBlockFormat(block_fmt)
            self.setTextCursor(cursor)

    def set_line_spacing(self, spacing: float) -> None:
        cursor = self.textCursor()
        block_fmt = cursor.blockFormat()
        block_fmt.setLineHeight(spacing * 100, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
        cursor.setBlockFormat(block_fmt)
        self.setTextCursor(cursor)

    def set_block_quote(self) -> None:
        cursor = self.textCursor()
        block_fmt = QTextBlockFormat()
        block_fmt.setIndent(1)
        char_fmt = QTextCharFormat()
        char_fmt.setProperty(QTextCharFormat.Property.FontItalic, True)
        cursor.mergeBlockFormat(block_fmt)
        cursor.mergeCharFormat(char_fmt)
        self.setTextCursor(cursor)

    def set_code_block(self) -> None:
        cursor = self.textCursor()
        block_fmt = QTextBlockFormat()
        block_fmt.setIndent(1)
        char_fmt = QTextCharFormat()
        char_fmt.setFontFamilies(["Consolas"])
        char_fmt.setFontPointSize(10)
        cursor.mergeBlockFormat(block_fmt)
        cursor.mergeCharFormat(char_fmt)
        self.setTextCursor(cursor)

    # ---------------------------------------------------------
    # Image insertion
    # ---------------------------------------------------------

    def insert_image_from_path(self, path: str, max_width: int = 600) -> None:
        """Insert an image at the cursor position, scaled to max_width."""
        from PySide6.QtGui import QPixmap

        pixmap = QPixmap(path)
        if pixmap.isNull():
            return

        # Scale down if wider than max_width
        if pixmap.width() > max_width:
            pixmap = pixmap.scaledToWidth(max_width, Qt.SmoothTransformation)

        self.textCursor().insertHtml(
            f'<img src="{image_data_url(pixmap.toImage())}" width="{pixmap.width()}" height="{pixmap.height()}">'
        )

    def canInsertFromMimeData(self, source):
        return source.hasImage() or super().canInsertFromMimeData(source)

    def insertFromMimeData(self, source):
        from PySide6.QtCore import QMimeData
        from PySide6.QtGui import QImage
        from PySide6.QtWidgets import QMessageBox

        try:
            if source.hasImage():
                image = QImage(source.imageData())
                self.textCursor().insertHtml(f'<img src="{image_data_url(image)}">')
            elif source.hasHtml():
                embedded = QMimeData()
                embedded.setHtml(portable_html(source.html()))
                super().insertFromMimeData(embedded)
            else:
                super().insertFromMimeData(source)
        except ValueError as exc:
            QMessageBox.warning(self, "Paste failed", str(exc))

    def insert_image_dialog(self) -> None:
        """Open file dialog and insert selected image."""
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Insert Image",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.svg *.webp);;All Files (*)",
        )
        if path:
            self.insert_image_from_path(path)

    # ---------------------------------------------------------
    # Table insertion
    # ---------------------------------------------------------

    def insert_table(self, rows: int, cols: int) -> None:
        """Insert an HTML table at the cursor position."""
        if rows < 1 or cols < 1:
            return

        # Build HTML table
        html = '<table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; width: 100%;">'
        for r in range(rows):
            html += "<tr>"
            for c in range(cols):
                tag = "th" if r == 0 else "td"
                html += f"<{tag}></{tag}>"
            html += "</tr>"
        html += "</table><p></p>"

        cursor = self.textCursor()
        cursor.insertHtml(html)

    def insert_horizontal_rule(self) -> None:
        cursor = self.textCursor()
        cursor.insertHtml("<hr>")

    def insert_link(self, url: str, text: str = "") -> None:
        fmt = QTextCharFormat()
        fmt.setAnchor(True)
        fmt.setAnchorHref(url)
        fmt.setFontUnderline(True)
        self.textCursor().insertText(text or url, fmt)

    # ---------------------------------------------------------
    # Format query helpers (for toolbar state reflection)
    # ---------------------------------------------------------

    def current_format(self) -> QTextCharFormat:
        return self.textCursor().charFormat()

    def is_bold(self) -> bool:
        return self.current_format().fontWeight() >= 700

    def is_italic(self) -> bool:
        return self.current_format().fontItalic()

    def is_underline(self) -> bool:
        return self.current_format().fontUnderline()

    def is_strikethrough(self) -> bool:
        return self.current_format().fontStrikeOut()

    def is_superscript(self) -> bool:
        return self.current_format().verticalAlignment() == QTextCharFormat.VerticalAlignment.AlignSuperScript

    def is_subscript(self) -> bool:
        return self.current_format().verticalAlignment() == QTextCharFormat.VerticalAlignment.AlignSubScript

    def current_font_family(self) -> str:
        families = self.current_format().fontFamilies()
        if families and len(families) > 0:
            return str(families[0])
        return self.document().defaultFont().family() or "Arial"

    def current_font_size(self) -> float:
        size = self.current_format().fontPointSize()
        default = self.document().defaultFont().pointSizeF()
        return size if size > 0 else (default if default > 0 else 12)

    def restore_document(self, html: str, path: str | None, dirty: bool) -> None:
        """Restore a tab without exposing editor internals to its controller."""
        self.setHtml(html)
        if not html:
            self.set_line_spacing(self.default_line_spacing)
        self._current_path = path
        self._dirty = dirty
        self.document().setModified(dirty)
        self.file_dirty_changed.emit(dirty)
        self.cursor_format_changed.emit()

    def mark_saved(self, path: str) -> None:
        self._current_path = path
        self._dirty = False
        self.document().setModified(False)
        self.file_dirty_changed.emit(False)

    def current_text_color(self):
        return self.current_format().foreground().color() if self.current_format().foreground().isValid() else None

    def current_highlight_color(self):
        return self.current_format().background().color() if self.current_format().background().isValid() else None

    # ---------------------------------------------------------
    # File handling
    # ---------------------------------------------------------

    def load_file(self, path: str) -> None:
        try:
            self.setHtml(load_as_html(path))

            self._current_path = path
            self._dirty = False
            self.file_dirty_changed.emit(False)
        except Exception as e:
            print(f"[SnapWord] Failed to load file: {e}")

    def save_file(self, path: str | None = None) -> None:
        if path is None:
            path = self._current_path
        if path is None:
            print("[SnapWord] No file path provided for save.")
            return

        if not confirm_conversion(self, path):
            return

        try:
            save_document(path, self.toHtml(), self.toPlainText())
            self.mark_saved(path)
        except Exception as e:
            print(f"[SnapWord] Failed to save file: {e}")

    # ---------------------------------------------------------
    # Export / Print
    # ---------------------------------------------------------

    def export_pdf(self) -> None:
        """Export the document to PDF via a file save dialog."""
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export as PDF",
            "",
            "PDF Files (*.pdf);;All Files (*)",
        )
        if not path:
            return

        from pathlib import Path

        from PySide6.QtPrintSupport import QPrinter
        from PySide6.QtWidgets import QMessageBox

        path = path if Path(path).suffix else path + ".pdf"
        try:
            with atomic_destination(path) as temporary:
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(str(temporary))
                self.document().print_(printer)
                if printer.printerState() == QPrinter.PrinterState.Error or temporary.stat().st_size == 0:
                    raise OSError("The PDF printer could not write the document.")
        except Exception as exc:
            QMessageBox.warning(self, "PDF export failed", str(exc))

    def export_document(self, path: str) -> bool:
        """Export without changing the source document's save point."""
        from PySide6.QtWidgets import QMessageBox
        if not confirm_conversion(self, path):
            return False
        try:
            save_document(path, self.toHtml(), self.toPlainText())
            return True
        except Exception as exc:
            QMessageBox.warning(self, "Export failed", str(exc))
            return False

    def print_document(self) -> None:
        """Print the document via the system print dialog."""
        from PySide6.QtPrintSupport import QPrintDialog, QPrinter

        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.Accepted:
            self.document().print_(printer)

    # ---------------------------------------------------------
    # Metrics
    # ---------------------------------------------------------

    def get_metrics(self) -> tuple[int, int]:
        text = self.toPlainText()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        return words, chars

    def current_path(self) -> str | None:
        return self._current_path

    def is_dirty(self) -> bool:
        return self._dirty

    # ---------------------------------------------------------
    # Internal hooks
    # ---------------------------------------------------------

    def _on_text_changed(self) -> None:
        self._modification_changed(self.document().isModified())

        words, chars = self.get_metrics()
        self.metrics_changed.emit(words, chars)

    def _on_cursor_moved(self) -> None:
        self.cursor_format_changed.emit()
