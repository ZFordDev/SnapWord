from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextBlockFormat, QTextCharFormat, QTextListFormat
from PySide6.QtWidgets import QTextEdit

from snapword.fonts import UI_TEXT, make_font


class SnapWordEditor(QTextEdit):
    metrics_changed = Signal(int, int)  # words, chars
    file_dirty_changed = Signal(bool)
    cursor_format_changed = Signal()  # emitted when cursor position/selection changes

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("RichTextEdit")
        self.setFont(make_font(UI_TEXT, 12))
        self.setPlaceholderText("Start typing your document here...")
        self.setAcceptRichText(True)

        self._current_path: str | None = None
        self._dirty: bool = False

        self.textChanged.connect(self._on_text_changed)
        self.cursorPositionChanged.connect(self._on_cursor_moved)

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
        block_fmt.setLineHeight(spacing, 1)  # 1 = ProportionalHeight
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
        char_fmt.setFontFamily("Consolas")
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

        # Save scaled image to a temp file for HTML embedding
        import tempfile
        from pathlib import Path

        suffix = Path(path).suffix or ".png"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            pixmap.save(tmp.name, suffix.lstrip(".").upper())
            tmp_path = tmp.name

        cursor = self.textCursor()
        cursor.insertHtml(f'<img src="{tmp_path}" width="{pixmap.width()}" height="{pixmap.height()}">')

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
        cursor = self.textCursor()
        if text:
            cursor.insertHtml(f'<a href="{url}">{text}</a>')
        else:
            cursor.insertHtml(f'<a href="{url}">{url}</a>')

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
        return "Arial"

    def current_font_size(self) -> int:
        size = self.current_format().fontPointSize()
        return int(size) if size > 0 else 12

    def current_text_color(self):
        return self.current_format().foreground().color() if self.current_format().foreground().isValid() else None

    def current_highlight_color(self):
        return self.current_format().background().color() if self.current_format().background().isValid() else None

    # ---------------------------------------------------------
    # File handling
    # ---------------------------------------------------------

    def load_file(self, path: str) -> None:
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()

            if path.endswith((".html", ".htm", ".docs")):
                self.setHtml(content)
            else:
                self.setPlainText(content)

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

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.toHtml())
            self._current_path = path
            self._dirty = False
            self.file_dirty_changed.emit(False)
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

        from PySide6.QtPrintSupport import QPrinter

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        self.document().print_(printer)

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
        if not self._dirty:
            self._dirty = True
            self.file_dirty_changed.emit(True)

        words, chars = self.get_metrics()
        self.metrics_changed.emit(words, chars)

    def _on_cursor_moved(self) -> None:
        self.cursor_format_changed.emit()
