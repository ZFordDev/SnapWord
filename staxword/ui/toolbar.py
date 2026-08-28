from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QFontComboBox,
    QInputDialog,
    QToolBar,
    QWidget,
)

from .editor import StaxWordEditor

_FONT_SIZES = [8, 9, 10, 10.5, 11, 12, 14, 16, 18, 20, 24, 28, 36, 48, 72]


class _ToolbarSection:
    """Tracks widgets belonging to one logical toolbar group."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.actions: list[QAction] = []
        self.widgets: list[QWidget] = []
        self.visible: bool = True


class StaxWordToolbar(QToolBar):
    def __init__(self, editor: StaxWordEditor, parent=None) -> None:
        super().__init__("Formatting", parent)
        self.setMovable(False)
        self.setFloatable(False)
        self._editor = editor
        self._updating_state = False

        self._sections: dict[str, _ToolbarSection] = {}
        self._separators: list = []

        self._build_ui()
        self._wire_signals()

    # ---------------------------------------------------------
    # Build
    # ---------------------------------------------------------

    def _build_ui(self) -> None:
        # --- Undo / Redo ---
        sec = self._section("undo_redo")
        self.action_undo = self._add_button(sec, "\u21b6", "Undo (Ctrl+Z)")
        self.action_redo = self._add_button(sec, "\u21b7", "Redo (Ctrl+Y)")
        self._sep()

        # --- Font family + size ---
        sec = self._section("font")
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(self._editor.currentFont())
        self.font_combo.setMaximumWidth(180)
        self.font_combo.currentFontChanged.connect(self._on_font_family_changed)
        sec.widgets.append(self.font_combo)
        self.addWidget(self.font_combo)

        self.size_combo = QComboBox()
        self.size_combo.setEditable(True)
        self.size_combo.setMaximumWidth(60)
        for s in _FONT_SIZES:
            self.size_combo.addItem(str(s), s)
        self.size_combo.setCurrentText(str(self._editor.current_font_size()))
        self.size_combo.currentTextChanged.connect(self._on_font_size_changed)
        sec.widgets.append(self.size_combo)
        self.addWidget(self.size_combo)
        self._sep()

        # --- Bold / Italic / Underline / Strikethrough ---
        sec = self._section("formatting")
        self.action_bold = self._add_checkable_button(sec, "B", "Bold (Ctrl+B)")
        self.action_italic = self._add_checkable_button(sec, "I", "Italic (Ctrl+I)")
        self.action_underline = self._add_checkable_button(sec, "U", "Underline (Ctrl+U)")
        self.action_strikethrough = self._add_checkable_button(sec, "S", "Strikethrough")
        self._sep()

        # --- Superscript / Subscript ---
        sec = self._section("super_sub")
        self.action_superscript = self._add_button(sec, "X\u00b2", "Superscript")
        self.action_subscript = self._add_button(sec, "X\u2082", "Subscript")
        self._sep()

        # --- Text color / Highlight ---
        sec = self._section("color")
        self.action_text_color = self._add_color_button(sec, "A", "Text color", is_highlight=False)
        self.action_highlight = self._add_color_button(sec, "\u2588", "Highlight color", is_highlight=True)
        self._sep()

        # --- Alignment ---
        sec = self._section("alignment")
        self.action_align_left = self._add_checkable_button(sec, "\u2261", "Align left")
        self.action_align_center = self._add_checkable_button(sec, "\u2261", "Align center")
        self.action_align_right = self._add_checkable_button(sec, "\u2261", "Align right")
        self.action_align_justify = self._add_checkable_button(sec, "\u2261", "Justify")
        self._sep()

        # --- Indent / Outdent ---
        sec = self._section("indent")
        self.action_indent = self._add_button(sec, "\u21e3", "Increase indent")
        self.action_outdent = self._add_button(sec, "\u21e1", "Decrease indent")
        self._sep()

        # --- Line spacing ---
        sec = self._section("spacing")
        self.spacing_combo = QComboBox()
        self.spacing_combo.setEditable(False)
        self.spacing_combo.setMaximumWidth(70)
        for label in ["1.0", "1.15", "1.5", "2.0"]:
            self.spacing_combo.addItem(label, float(label))
        self.spacing_combo.setCurrentText("1.0")
        self.spacing_combo.currentTextChanged.connect(self._on_line_spacing_changed)
        sec.widgets.append(self.spacing_combo)
        self.addWidget(self.spacing_combo)
        self._sep()

        # --- Lists ---
        sec = self._section("lists")
        self.action_bullet_list = self._add_button(sec, "\u2022", "Bullet list")
        self.action_numbered_list = self._add_button(sec, "1.", "Numbered list")
        self._sep()

        # --- Block quote / Code block ---
        sec = self._section("blocks")
        self.action_block_quote = self._add_button(sec, "\u201c", "Block quote")
        self.action_code_block = self._add_button(sec, "</>", "Code block")
        self._sep()

        # --- Insert ---
        sec = self._section("insert")
        self.action_insert_link = self._add_button(sec, "\U0001f517", "Insert link")
        self.action_insert_hr = self._add_button(sec, "\u2015", "Horizontal rule")
        self.action_insert_image = self._add_button(sec, "\U0001f5bc", "Insert image")
        self.action_insert_table = self._add_button(sec, "\u2a01", "Insert table")
        self._sep()

        # --- Export / Print ---
        sec = self._section("export")
        self.action_print = self._add_button(sec, "\U0001f5a8", "Print")
        self.action_export_pdf = self._add_button(sec, "\U0001f4c4", "Export PDF")

        # --- Clear formatting ---
        self._sep()
        sec = self._section("clear")
        self.action_clear = self._add_button(sec, "\u2716", "Clear formatting")

    # ---------------------------------------------------------
    # Section management
    # ---------------------------------------------------------

    def _section(self, name: str) -> _ToolbarSection:
        if name not in self._sections:
            self._sections[name] = _ToolbarSection(name)
        return self._sections[name]

    def _sep(self) -> None:
        sep = self.addSeparator()
        self._separators.append(sep)

    def toggle_section(self, name: str, visible: bool) -> None:
        """Show or hide a named toolbar section."""
        sec = self._sections.get(name)
        if not sec:
            return
        sec.visible = visible
        for action in sec.actions:
            action.setVisible(visible)
        for widget in sec.widgets:
            widget.setVisible(visible)

    def section_names(self) -> list[str]:
        return list(self._sections.keys())

    def is_section_visible(self, name: str) -> bool:
        sec = self._sections.get(name)
        return sec.visible if sec else False

    # ---------------------------------------------------------
    # Wire signals
    # ---------------------------------------------------------

    def _wire_signals(self) -> None:
        self.action_undo.triggered.connect(self._editor.undo)
        self.action_redo.triggered.connect(self._editor.redo)

        self.action_bold.triggered.connect(self._on_bold)
        self.action_italic.triggered.connect(self._on_italic)
        self.action_underline.triggered.connect(self._on_underline)
        self.action_strikethrough.triggered.connect(self._on_strikethrough)
        self.action_superscript.triggered.connect(self._on_superscript)
        self.action_subscript.triggered.connect(self._on_subscript)

        self.action_align_left.triggered.connect(lambda: self._editor.set_alignment(Qt.AlignLeft))
        self.action_align_center.triggered.connect(lambda: self._editor.set_alignment(Qt.AlignCenter))
        self.action_align_right.triggered.connect(lambda: self._editor.set_alignment(Qt.AlignRight))
        self.action_align_justify.triggered.connect(lambda: self._editor.set_alignment(Qt.AlignJustify))

        self.action_indent.triggered.connect(self._editor.set_indent)
        self.action_outdent.triggered.connect(self._editor.set_outdent)

        self.action_bullet_list.triggered.connect(self._editor.set_bullet_list)
        self.action_numbered_list.triggered.connect(self._editor.set_numbered_list)

        self.action_block_quote.triggered.connect(self._editor.set_block_quote)
        self.action_code_block.triggered.connect(self._editor.set_code_block)

        self.action_insert_link.triggered.connect(self._on_insert_link)
        self.action_insert_hr.triggered.connect(self._editor.insert_horizontal_rule)
        self.action_insert_image.triggered.connect(self._editor.insert_image_dialog)
        self.action_insert_table.triggered.connect(self._on_insert_table)

        self.action_clear.triggered.connect(self._editor.clear_formatting)

        self.action_print.triggered.connect(self._editor.print_document)
        self.action_export_pdf.triggered.connect(self._editor.export_pdf)

        self._editor.cursor_format_changed.connect(self._update_state_from_cursor)

    # ---------------------------------------------------------
    # Slot handlers
    # ---------------------------------------------------------

    def _on_bold(self) -> None:
        self._editor.set_bold(not self._editor.is_bold())

    def _on_italic(self) -> None:
        self._editor.set_italic(not self._editor.is_italic())

    def _on_underline(self) -> None:
        self._editor.set_underline(not self._editor.is_underline())

    def _on_strikethrough(self) -> None:
        self._editor.set_strikethrough(not self._editor.is_strikethrough())

    def _on_superscript(self) -> None:
        self._editor.set_superscript(not self._editor.is_superscript())

    def _on_subscript(self) -> None:
        self._editor.set_subscript(not self._editor.is_subscript())

    def _on_font_family_changed(self, font) -> None:
        if not self._updating_state:
            self._editor.set_font_family(font.family())

    def _on_font_size_changed(self, text: str) -> None:
        if not self._updating_state:
            import contextlib
            with contextlib.suppress(ValueError):
                self._editor.set_font_size(float(text))

    def _on_line_spacing_changed(self, text: str) -> None:
        if not self._updating_state:
            import contextlib
            with contextlib.suppress(ValueError):
                self._editor.set_line_spacing(float(text))

    def _on_insert_link(self) -> None:
        url, ok = QInputDialog.getText(self, "Insert Link", "URL:")
        if ok and url:
            text, ok2 = QInputDialog.getText(self, "Insert Link", "Display text (optional):")
            self._editor.insert_link(url, text if ok2 else "")

    def _on_insert_table(self) -> None:
        from .tablepicker import TablePickerDialog

        dialog = TablePickerDialog(self)
        dialog.table_selected.connect(self._editor.insert_table)
        dialog.exec()

    def _on_text_color(self) -> None:
        color = QColorDialog.getColor(self._editor.current_text_color() or QColor(Qt.black), self, "Text Color")
        if color.isValid():
            self._editor.set_text_color(color)

    def _on_highlight_color(self) -> None:
        color = QColorDialog.getColor(
            self._editor.current_highlight_color() or QColor(Qt.yellow), self, "Highlight Color"
        )
        if color.isValid():
            self._editor.set_highlight_color(color)

    # ---------------------------------------------------------
    # Toolbar state sync
    # ---------------------------------------------------------

    def _update_state_from_cursor(self) -> None:
        if self._updating_state:
            return
        self._updating_state = True
        try:
            self.action_bold.setChecked(self._editor.is_bold())
            self.action_italic.setChecked(self._editor.is_italic())
            self.action_underline.setChecked(self._editor.is_underline())
            self.action_strikethrough.setChecked(self._editor.is_strikethrough())

            family = self._editor.current_font_family()
            from PySide6.QtGui import QFont
            self.font_combo.setCurrentFont(QFont(family))

            size = self._editor.current_font_size()
            self.size_combo.setCurrentText(str(size))

            align = self._editor.alignment()
            self.action_align_left.setChecked(align & Qt.AlignLeft)
            self.action_align_center.setChecked(align & Qt.AlignHCenter)
            self.action_align_right.setChecked(align & Qt.AlignRight)
            self.action_align_justify.setChecked(align & Qt.AlignJustify)
        finally:
            self._updating_state = False

    # ---------------------------------------------------------
    # Button factories
    # ---------------------------------------------------------

    def _add_button(self, sec: _ToolbarSection, label: str, tooltip: str) -> QAction:
        action = QAction(label, self)
        action.setToolTip(tooltip)
        sec.actions.append(action)
        self.addAction(action)
        return action

    def _add_checkable_button(self, sec: _ToolbarSection, label: str, tooltip: str) -> QAction:
        action = QAction(label, self)
        action.setCheckable(True)
        action.setToolTip(tooltip)
        sec.actions.append(action)
        self.addAction(action)
        return action

    def _add_color_button(self, sec: _ToolbarSection, label: str, tooltip: str, is_highlight: bool = False) -> QAction:
        action = QAction(label, self)
        action.setToolTip(tooltip)
        if is_highlight:
            action.triggered.connect(self._on_highlight_color)
        else:
            action.triggered.connect(self._on_text_color)
        sec.actions.append(action)
        self.addAction(action)
        return action
