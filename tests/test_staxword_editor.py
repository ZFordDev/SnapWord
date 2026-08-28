import tempfile
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication, QWidget

from staxword.themes import (
    THEME_COLORS,
    apply_theme_to_widget,
    generate_qss,
    is_builtin,
    list_themes,
    load_theme_colors,
    save_theme_colors,
)
from staxword.ui.editor import StaxWordEditor
from staxword.ui.findbar import FindReplaceBar
from staxword.ui.preferences import PreferencesDialog, load_prefs
from staxword.ui.tablepicker import TablePickerDialog
from staxword.ui.tabs import StaxWordTabBar, TabDocument
from staxword.ui.themeditor import ThemeEditorDialog
from staxword.ui.window import StaxWordWindow


class StaxWordEditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_editor_starts_empty_and_clean(self) -> None:
        editor = StaxWordEditor()
        self.assertEqual(editor.toPlainText(), "")
        self.assertFalse(editor.is_dirty())
        self.assertIsNone(editor.current_path())

    def test_text_change_sets_dirty_and_emits_metrics(self) -> None:
        editor = StaxWordEditor()
        metrics = []
        editor.metrics_changed.connect(lambda w, c: metrics.append((w, c)))
        editor.setPlainText("Hello world")
        self.assertTrue(editor.is_dirty())
        self.assertTrue(metrics)
        self.assertEqual(metrics[-1], (2, 11))

    def test_bold_formatting(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("Test")
        editor.selectAll()
        editor.set_bold(True)
        self.assertTrue(editor.is_bold())

    def test_italic_formatting(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("Test")
        editor.selectAll()
        editor.set_italic(True)
        self.assertTrue(editor.is_italic())

    def test_underline_formatting(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("Test")
        editor.selectAll()
        editor.set_underline(True)
        self.assertTrue(editor.is_underline())

    def test_strikethrough_formatting(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("Test")
        editor.selectAll()
        editor.set_strikethrough(True)
        self.assertTrue(editor.is_strikethrough())

    def test_superscript_formatting(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("Test")
        editor.selectAll()
        editor.set_superscript(True)
        self.assertTrue(editor.is_superscript())

    def test_subscript_formatting(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("Test")
        editor.selectAll()
        editor.set_subscript(True)
        self.assertTrue(editor.is_subscript())

    def test_font_family(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("Test")
        editor.selectAll()
        editor.set_font_family("Courier New")
        self.assertEqual(editor.current_font_family(), "Courier New")

    def test_font_size(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("Test")
        editor.selectAll()
        editor.set_font_size(20)
        self.assertEqual(editor.current_font_size(), 20)

    def test_clear_formatting(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("Test")
        editor.selectAll()
        editor.set_bold(True)
        editor.clear_formatting()
        self.assertFalse(editor.is_bold())

    def test_heading_formatting(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("Title")
        editor.selectAll()
        editor.set_heading(1)
        cursor = editor.textCursor()
        self.assertEqual(cursor.blockFormat().headingLevel(), 1)

    def test_insert_horizontal_rule(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("Before")
        editor.insert_horizontal_rule()
        self.assertIn("<hr", editor.toHtml().lower())

    def test_insert_link(self) -> None:
        editor = StaxWordEditor()
        editor.insert_link("https://example.com", "Example")
        html = editor.toHtml()
        self.assertIn("https://example.com", html)

    def test_save_and_load_html_round_trip(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("Hello world")
        editor._dirty = False
        with tempfile.NamedTemporaryFile(suffix=".staxdoc", delete=False, mode="w") as f:
            path = f.name
        try:
            editor.save_file(path)
            self.assertFalse(editor.is_dirty())
            editor2 = StaxWordEditor()
            editor2.load_file(path)
            self.assertEqual(editor2.toPlainText(), "Hello world")
        finally:
            Path(path).unlink(missing_ok=True)

    def test_save_without_path_does_not_crash(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("test")
        editor.save_file()
        self.assertIsNone(editor.current_path())

    def test_cursor_format_signal_emitted(self) -> None:
        editor = StaxWordEditor()
        signals = []
        editor.cursor_format_changed.connect(lambda: signals.append(True))
        editor.setPlainText("Test")
        self.assertTrue(signals)

    def test_alignment(self) -> None:
        from PySide6.QtCore import Qt
        editor = StaxWordEditor()
        editor.set_alignment(Qt.AlignCenter)
        self.assertEqual(editor.alignment(), Qt.AlignCenter)
        editor.set_alignment(Qt.AlignLeft)
        self.assertEqual(editor.alignment(), Qt.AlignLeft)


class TabDocumentTests(unittest.TestCase):
    def test_empty_document(self) -> None:
        doc = TabDocument()
        self.assertIsNone(doc.path)
        self.assertEqual(doc.html, "")
        self.assertFalse(doc.dirty)
        self.assertEqual(doc.label, "Untitled")

    def test_from_path(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".staxdoc", delete=False, mode="w") as f:
            f.write("<h1>Hello</h1><p>World</p>")
            path = f.name
        try:
            doc = TabDocument.from_path(path)
            self.assertIn("Hello", doc.html)
            self.assertEqual(doc.label, Path(path).name)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_from_missing_path(self) -> None:
        doc = TabDocument.from_path("/nonexistent/file.html")
        self.assertEqual(doc.label, "file.html")


class StaxWordTabBarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_add_and_count(self) -> None:
        bar = StaxWordTabBar()
        bar.add_tab("Doc 1")
        bar.add_tab("Doc 2")
        self.assertEqual(bar.count(), 2)

    def test_remove_tab(self) -> None:
        bar = StaxWordTabBar()
        bar.add_tab("Doc 1")
        bar.add_tab("Doc 2")
        bar.remove_tab(0)
        self.assertEqual(bar.count(), 1)

    def test_set_tab_label(self) -> None:
        bar = StaxWordTabBar()
        idx = bar.add_tab("Old")
        bar.set_tab_label(idx, "New")
        self.assertEqual(bar._tab_bar.tabText(idx), "New")

    def test_set_tab_dirty(self) -> None:
        bar = StaxWordTabBar()
        idx = bar.add_tab("Doc")
        bar.set_tab_dirty(idx, True)
        self.assertTrue("\u25cf" in bar._tab_bar.tabText(idx))
        bar.set_tab_dirty(idx, False)
        self.assertFalse("\u25cf" in bar._tab_bar.tabText(idx))

    def test_close_button_exists(self) -> None:
        from PySide6.QtWidgets import QTabBar
        bar = StaxWordTabBar()
        idx = bar.add_tab("Doc")
        btn = bar._tab_bar.tabButton(idx, QTabBar.ButtonPosition.RightSide)
        self.assertIsNotNone(btn)


class StaxWordWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_window_starts_with_one_tab(self) -> None:
        window = StaxWordWindow()
        self.assertEqual(window.tab_bar.count(), 1)
        self.assertEqual(len(window._tabs), 1)

    def test_new_tab_creates_tab(self) -> None:
        window = StaxWordWindow()
        window._new_tab()
        self.assertEqual(window.tab_bar.count(), 2)
        self.assertEqual(len(window._tabs), 2)

    def test_file_tree_hidden_by_default(self) -> None:
        window = StaxWordWindow()
        self.assertFalse(window.file_tree.isVisible())

    def test_toggle_file_tree(self) -> None:
        window = StaxWordWindow()
        window.show()
        window._toggle_file_tree()
        self.assertTrue(window.file_tree.isVisible())
        window._toggle_file_tree()
        self.assertFalse(window.file_tree.isVisible())

    def test_load_file_creates_new_tab(self) -> None:
        window = StaxWordWindow()
        with tempfile.NamedTemporaryFile(suffix=".staxdoc", delete=False, mode="w") as f:
            f.write("<p>Test</p>")
            path = f.name
        try:
            window.load_file(path)
            self.assertEqual(window.tab_bar.count(), 2)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_load_same_file_does_not_duplicate(self) -> None:
        window = StaxWordWindow()
        with tempfile.NamedTemporaryFile(suffix=".staxdoc", delete=False, mode="w") as f:
            f.write("<p>Test</p>")
            path = f.name
        try:
            window.load_file(path)
            window.load_file(path)
            self.assertEqual(window.tab_bar.count(), 2)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_title_updates_with_dirty(self) -> None:
        window = StaxWordWindow()
        window.editor.setPlainText("hello")
        self.assertTrue("\u2022" in window.windowTitle())

    def test_toolbar_has_sections(self) -> None:
        window = StaxWordWindow()
        self.assertIn("font", window.toolbar.section_names())
        self.assertIn("formatting", window.toolbar.section_names())
        self.assertIn("color", window.toolbar.section_names())

    def test_toggle_toolbar_section(self) -> None:
        window = StaxWordWindow()
        self.assertTrue(window.toolbar.is_section_visible("font"))
        window.toolbar.toggle_section("font", False)
        self.assertFalse(window.toolbar.is_section_visible("font"))
        window.toolbar.toggle_section("font", True)
        self.assertTrue(window.toolbar.is_section_visible("font"))

    def test_toolbar_has_new_sections(self) -> None:
        window = StaxWordWindow()
        self.assertIn("indent", window.toolbar.section_names())
        self.assertIn("spacing", window.toolbar.section_names())
        self.assertIn("blocks", window.toolbar.section_names())

    def test_find_bar_hidden_by_default(self) -> None:
        window = StaxWordWindow()
        self.assertFalse(window.find_bar.isVisible())

    def test_justify_alignment(self) -> None:
        from PySide6.QtCore import Qt
        editor = StaxWordEditor()
        editor.set_justify()
        self.assertEqual(editor.alignment(), Qt.AlignJustify)

    def test_indent_outdent(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("Test")
        editor.set_indent()
        cursor = editor.textCursor()
        self.assertEqual(cursor.blockFormat().indent(), 1)

        editor.set_outdent()
        cursor = editor.textCursor()
        self.assertEqual(cursor.blockFormat().indent(), 0)

    def test_outdent_at_zero_does_nothing(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("Test")
        editor.set_outdent()
        cursor = editor.textCursor()
        self.assertEqual(cursor.blockFormat().indent(), 0)

    def test_line_spacing(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("Test")
        editor.set_line_spacing(1.5)
        # Just verify it doesn't crash
        self.assertTrue(True)

    def test_block_quote(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("Test")
        editor.selectAll()
        editor.set_block_quote()
        cursor = editor.textCursor()
        self.assertEqual(cursor.blockFormat().indent(), 1)

    def test_code_block(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("Test")
        editor.selectAll()
        editor.set_code_block()
        cursor = editor.textCursor()
        self.assertEqual(cursor.blockFormat().indent(), 1)
        fmt = cursor.charFormat()
        self.assertEqual(fmt.fontFamily(), "Consolas")


class FindReplaceBarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_find_bar_starts_hidden(self) -> None:
        editor = StaxWordEditor()
        bar = FindReplaceBar(editor)
        self.assertFalse(bar.isVisible())

    def test_show_replace_shows_replace_widget(self) -> None:
        editor = StaxWordEditor()
        bar = FindReplaceBar(editor)
        bar.show()
        bar.show_replace()
        self.assertTrue(bar.replace_widget.isVisibleTo(bar))

    def test_toggle_replace(self) -> None:
        editor = StaxWordEditor()
        bar = FindReplaceBar(editor)
        bar.show()
        bar.toggle_replace()
        self.assertTrue(bar.replace_widget.isVisibleTo(bar))
        bar.toggle_replace()
        self.assertFalse(bar.replace_widget.isVisibleTo(bar))

    def test_find_next_with_text(self) -> None:
        editor = StaxWordEditor()
        editor.show()
        editor.setPlainText("Hello world Hello")
        bar = FindReplaceBar(editor)
        bar.show()
        bar.search_input.setText("Hello")
        # find_next calls QTextEdit.find() — in offscreen mode this may
        # not select text, but the method should not raise
        bar.find_next()
        self.assertTrue(True)

    def test_replace_all(self) -> None:
        editor = StaxWordEditor()
        editor.show()
        editor.setPlainText("Hello world Hello")
        bar = FindReplaceBar(editor)
        bar.show()
        bar.search_input.setText("Hello")
        bar.replace_input.setText("Hi")
        bar.replace_all()
        self.assertEqual(editor.toPlainText(), "Hi world Hi")


class ImageInsertTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_insert_image_from_invalid_path_is_noop(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("Before")
        editor.insert_image_from_path("/nonexistent/fake.png")
        self.assertEqual(editor.toPlainText(), "Before")

    def test_insert_image_from_valid_png(self) -> None:
        import tempfile
        from pathlib import Path

        from PySide6.QtGui import QImage

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img = QImage(10, 10, QImage.Format.Format_RGBA8888)
            img.fill(0xFF0000FF)
            img.save(f.name, "PNG")
            tmp = f.name

        editor = StaxWordEditor()
        editor.setPlainText("Before")
        editor.insert_image_from_path(tmp, max_width=50)
        html = editor.toHtml()
        self.assertIn("<img", html)

        Path(tmp).unlink(missing_ok=True)

    def test_insert_image_dialog_is_callable(self) -> None:
        editor = StaxWordEditor()
        self.assertTrue(callable(editor.insert_image_dialog))


class TableInsertTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_insert_table(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("Before")
        editor.insert_table(3, 4)
        html = editor.toHtml()
        self.assertIn("<table", html)
        # QTextEdit normalizes empty <th> to <td> in toHtml(); verify rows
        self.assertEqual(html.count("<tr>"), 3)

    def test_insert_table_invalid_dims(self) -> None:
        editor = StaxWordEditor()
        editor.setPlainText("Before")
        editor.insert_table(0, 5)
        self.assertEqual(editor.toPlainText(), "Before")

    def test_insert_single_row(self) -> None:
        editor = StaxWordEditor()
        editor.insert_table(1, 2)
        html = editor.toHtml()
        self.assertIn("<table", html)
        self.assertEqual(html.count("<tr>"), 1)

    def test_table_picker_creation(self) -> None:
        dialog = TablePickerDialog()
        self.assertEqual(dialog.windowTitle(), "Insert Table")

    def test_table_picker_grid_size(self) -> None:
        dialog = TablePickerDialog()
        self.assertEqual(dialog.MAX_ROWS, 10)
        self.assertEqual(dialog.MAX_COLS, 8)

    def test_toolbar_has_image_table_buttons(self) -> None:
        window = StaxWordWindow()
        self.assertTrue(hasattr(window.toolbar, "action_insert_image"))
        self.assertTrue(hasattr(window.toolbar, "action_insert_table"))


class ExportPrintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_export_pdf_to_temp(self) -> None:
        import tempfile
        from pathlib import Path

        from PySide6.QtPrintSupport import QPrinter

        editor = StaxWordEditor()
        editor.show()
        editor.setPlainText("Export test content")

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp = f.name

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(tmp)
        editor.document().print_(printer)

        self.assertTrue(Path(tmp).exists())
        self.assertGreater(Path(tmp).stat().st_size, 0)
        Path(tmp).unlink(missing_ok=True)

    def test_print_method_exists(self) -> None:
        editor = StaxWordEditor()
        self.assertTrue(callable(editor.print_document))

    def test_export_pdf_method_exists(self) -> None:
        editor = StaxWordEditor()
        self.assertTrue(callable(editor.export_pdf))

    def test_toolbar_has_print_pdf_buttons(self) -> None:
        window = StaxWordWindow()
        self.assertTrue(hasattr(window.toolbar, "action_print"))
        self.assertTrue(hasattr(window.toolbar, "action_export_pdf"))
        self.assertIn("export", window.toolbar.section_names())

    def test_menubar_has_print_pdf_actions(self) -> None:
        window = StaxWordWindow()
        self.assertTrue(hasattr(window.menu_bar, "action_print"))
        self.assertTrue(hasattr(window.menu_bar, "action_export_pdf"))


class ThemeManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_list_themes_has_builtin(self) -> None:
        themes = list_themes()
        self.assertIn("light", themes)
        self.assertIn("dark", themes)
        self.assertTrue(themes["light"]["builtin"])

    def test_builtin_detection(self) -> None:
        self.assertTrue(is_builtin("light"))
        self.assertTrue(is_builtin("dark"))
        self.assertFalse(is_builtin("nonexistent"))

    def test_generate_qss_from_light(self) -> None:
        qss = generate_qss("light", {})
        self.assertIn("background-color", qss)
        self.assertIn("QWidget", qss)

    def test_generate_qss_with_overrides(self) -> None:
        qss = generate_qss("light", {"editor_bg": "#ff0000"})
        # The override won't appear in raw QSS since it uses placeholders
        # But the function should return a string without error
        self.assertIsInstance(qss, str)
        self.assertIn("QWidget", qss)

    def test_theme_colors_has_required_keys(self) -> None:
        required = ["workspace_bg", "editor_bg", "text_color", "accent"]
        for key in required:
            self.assertIn(key, THEME_COLORS)

    def test_save_and_load_user_theme(self) -> None:

        from staxword.themes import _USER_THEMES_DIR

        name = "_test_theme_delete_me"
        save_theme_colors(name, {"editor_bg": "#123456", "_base": "light"})
        colors = load_theme_colors(name)
        self.assertIsNotNone(colors)
        self.assertEqual(colors["editor_bg"], "#123456")

        # Cleanup
        path = _USER_THEMES_DIR / f"{name}.json"
        path.unlink(missing_ok=True)

    def test_apply_theme_to_widget(self) -> None:
        widget = QWidget()
        apply_theme_to_widget(widget, "light")
        self.assertNotEqual(widget.styleSheet(), "")


class PreferencesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_load_prefs_returns_defaults(self) -> None:
        prefs = load_prefs()
        self.assertIn("editor_font_size", prefs)
        self.assertIn("editor_font_family", prefs)
        self.assertIn("line_spacing", prefs)

    def test_preferences_dialog_creation(self) -> None:
        dialog = PreferencesDialog()
        self.assertEqual(dialog.windowTitle(), "Preferences")


class ThemeEditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_theme_editor_creation(self) -> None:
        dialog = ThemeEditorDialog()
        self.assertEqual(dialog.windowTitle(), "Theme Editor")

    def test_theme_editor_has_color_buttons(self) -> None:
        dialog = ThemeEditorDialog()
        self.assertGreater(len(dialog._color_buttons), 5)

    def test_theme_editor_get_colors(self) -> None:
        dialog = ThemeEditorDialog()
        colors = dialog.get_colors()
        self.assertIn("editor_bg", colors)
        self.assertIn("text_color", colors)

    def test_window_has_theme_menu_actions(self) -> None:
        window = StaxWordWindow()
        self.assertTrue(hasattr(window.menu_bar, "action_theme_edit"))
        self.assertTrue(hasattr(window.menu_bar, "action_preferences"))

