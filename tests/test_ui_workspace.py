"""Regression coverage for modular UI ownership, persistence and document safety."""

from unittest.mock import patch

import pytest
from PySide6.QtCore import QByteArray, QPoint, QSettings, Qt, qInstallMessageHandler
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QTabBar, QToolBar

from snapword.themes import generate_qss
from snapword.ui.window import SnapWordWindow


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def settings(tmp_path):
    return QSettings(str(tmp_path / "workspace.ini"), QSettings.Format.IniFormat)


@pytest.fixture
def window(app, settings):
    widget = SnapWordWindow(settings=settings)
    widget.show()
    app.processEvents()
    yield widget
    widget.hide()
    widget.deleteLater()
    app.processEvents()


def test_no_hidden_monolithic_toolbar_and_shared_commands(window):
    assert set(window.findChildren(QToolBar)) == set(window.toolbar_sections.values())
    assert window.menu_bar.action_print is window.toolbar.action_print
    assert window.menu_bar.action_export_pdf is window.toolbar.action_export_pdf
    window.toolbar_sections["formatting"].hide()
    window.actions["format.bold"].trigger()
    assert window.editor.is_bold()
    window.actions["format.bold"].trigger()
    assert not window.editor.is_bold()


def test_visibility_does_not_hide_shared_menu_action(window):
    bar = window.toolbar_sections["insert"]
    toggle = bar.toggleViewAction()
    toggle.trigger()
    assert bar.isHidden()
    assert not toggle.isChecked()
    assert window.actions["insert.image"].isVisible()
    bar.show()
    assert toggle.isChecked()


def test_restore_layout_after_docks_exist(window, app, settings):
    bar = window.toolbar_sections["font"]
    window.addToolBar(Qt.BottomToolBarArea, bar)
    window.toolbar_sections["insert"].hide()
    window.addDockWidget(Qt.RightDockWidgetArea, window.file_tree_dock)
    window.file_tree_dock.show()
    window.workspace_layout.save()
    restored = SnapWordWindow(settings=settings)
    restored.show()
    app.processEvents()
    try:
        assert restored.toolBarArea(restored.toolbar_sections["font"]) == Qt.BottomToolBarArea
        assert restored.toolbar_sections["insert"].isHidden()
        assert restored.dockWidgetArea(restored.file_tree_dock) == Qt.RightDockWidgetArea
        assert restored.file_tree_dock.isVisible()
        assert restored.menu_bar.action_view_filetree.isChecked()
    finally:
        restored.hide()
        restored.deleteLater()


def test_reset_restores_order_and_defaults(window, app):
    window.addToolBar(Qt.BottomToolBarArea, window.toolbar_sections["font"])
    window.toolbar_sections["formatting"].hide()
    window.toolbar_sections["super_sub"].show()
    window.file_tree_dock.show()
    window._reset_workspace_layout()
    app.processEvents()
    for row in window.toolbar.DEFAULT_ROWS:
        bars = [window.toolbar_sections[name] for name in row]
        assert all(bar.isVisible() for bar in bars)
        assert all(window.toolBarArea(bar) == Qt.TopToolBarArea for bar in bars)
        assert [bar.x() for bar in bars] == sorted(bar.x() for bar in bars)
    assert window.toolBarBreak(window.toolbar_sections["color"])
    assert window.toolbar_sections["super_sub"].isHidden()
    assert window.file_tree_dock.isHidden()


def test_corrupt_saved_layout_falls_back(app, settings):
    settings.setValue("toolbar_layout", QByteArray(b"invalid"))
    widget = SnapWordWindow(settings=settings)
    assert not widget.toolbar_sections["font"].isHidden()
    widget.deleteLater()


def test_page_and_first_line_stay_at_top_on_resize(window, app):
    for width, height in ((1200, 900), (800, 600), (1500, 1100)):
        window.resize(width, height)
        for _ in range(3):
            app.processEvents()
        assert window._page_container.y() == 0
        assert window.editor.y() == 0
        top = window.editor.viewport().mapTo(window._page_container, window.editor.cursorRect().topLeft())
        assert 20 <= top.y() < 80


def test_document_growth_and_shrink_update_outer_scroll(window, app):
    window.editor.setPlainText("A line\n" * 200)
    for _ in range(4):
        app.processEvents()
    assert window.page_scroll_area.verticalScrollBar().maximum() > 0
    cursor = window.editor.textCursor()
    cursor.movePosition(QTextCursor.End)
    window.editor.setTextCursor(cursor)
    app.processEvents()
    assert window.page_scroll_area.verticalScrollBar().value() > 0
    window.editor.setPlainText("")
    for _ in range(4):
        app.processEvents()
    assert window.page_scroll_area.verticalScrollBar().maximum() == 0


def test_cursor_sync_preserves_fractional_font_size(window):
    window.editor.set_font_size(10.5)
    window.editor.set_superscript(True)
    assert window.toolbar_sections["font"].size.currentText() == "10.5"
    assert window.actions["format.superscript"].isChecked()
    window.editor.set_line_spacing(1.5)
    assert window.editor.textCursor().blockFormat().lineHeight() == 150
    window.toolbar_sections["spacing"].sync()
    assert window.toolbar_sections["spacing"].combo.currentData() == 1.5


def test_reordering_and_closing_tabs_preserves_document_identity(window):
    window.editor.setPlainText("first")
    window.documents.new()
    window.editor.setPlainText("second")
    window.tab_bar._tab_bar.moveTab(1, 0)
    assert window.editor.toPlainText() == "second"
    assert window.documents.active == 0
    window.tab_bar.set_current_index(1)
    assert window.editor.toPlainText() == "first"
    button = window.tab_bar._tab_bar.tabButton(0, QTabBar.RightSide)
    with patch.object(QMessageBox, "question", return_value=QMessageBox.Discard):
        button.click()
    assert window.editor.toPlainText() == "first"
    assert len(window.documents.tabs) == 1


def test_save_inactive_tab_uses_its_own_content(window, tmp_path):
    window.editor.setPlainText("first")
    window.documents.new()
    window.editor.setPlainText("second")
    path = str(tmp_path / "first.txt")
    with (patch.object(QFileDialog, "getSaveFileName", return_value=(path, "Plain Text")),
          patch.object(QMessageBox, "warning", return_value=QMessageBox.Yes)):
        assert window.documents.save_tab(0)
    assert (tmp_path / "first.txt").read_text(encoding="utf-8") == "first"
    assert window.editor.toPlainText() == "second"
    assert window.editor.is_dirty()


def test_failed_or_cancelled_save_prevents_close(window):
    window.editor.setPlainText("unsaved")
    with (
        patch.object(QMessageBox, "question", return_value=QMessageBox.SaveAll),
        patch.object(QFileDialog, "getSaveFileName", return_value=("", "")),
    ):
        assert not window.documents.confirm_close()
    assert window.editor.is_dirty()


def test_theme_overrides_are_applied():
    qss = generate_qss("dark", {"editor_bg": "#123456"})
    assert "#123456" in qss
    assert "{editor_bg}" not in qss
    assert "{page_vertical_padding}" not in qss


def test_native_handle_drag_float_restore_and_redock(window, app, settings):
    bar = window.toolbar_sections["font"]
    QTest.mousePress(bar, Qt.LeftButton, Qt.NoModifier, QPoint(5, 15))
    QTest.mouseMove(bar, QPoint(70, 250), 20)
    QTest.mouseRelease(bar, Qt.LeftButton, Qt.NoModifier, QPoint(70, 250))
    app.processEvents()
    assert bar.isFloating()
    assert bar.parentWidget() is window
    window.workspace_layout.save()
    restored = SnapWordWindow(settings=settings)
    restored.show()
    app.processEvents()
    try:
        floating = restored.toolbar_sections["font"]
        assert floating.isFloating()
        floating.dock()
        app.processEvents()
        assert not floating.isFloating()
        restored._reset_workspace_layout()
        assert restored.toolBarArea(floating) == Qt.TopToolBarArea
    finally:
        restored.hide()
        restored.deleteLater()
        bar.dock()


def test_save_failure_preserves_dirty_state(window, tmp_path):
    window.editor.setPlainText("unsaved")
    with (
        patch.object(QFileDialog, "getSaveFileName", return_value=(str(tmp_path / "broken.docs"), "")),
        patch("snapword.ui.documents.save_document", side_effect=OSError("disk full")),
        patch.object(QMessageBox, "warning"),
    ):
        assert not window.documents.save_tab(0)
    assert window.documents.tabs[0].dirty
    assert window.editor.is_dirty()


def test_cancel_close_does_not_persist_layout(window, settings):
    window.editor.setPlainText("unsaved")
    with patch.object(QMessageBox, "question", return_value=QMessageBox.Cancel):
        assert not window.close()
    assert not settings.contains("toolbar_layout")


def test_switching_tabs_restores_scroll_position(window, app):
    window.editor.setPlainText("long document\n" * 200)
    for _ in range(5):
        app.processEvents()
    scroll = window.page_scroll_area.verticalScrollBar()
    scroll.setValue(scroll.maximum() // 2)
    saved = scroll.value()
    window.documents.new()
    for _ in range(5):
        app.processEvents()
    window.tab_bar.set_current_index(0)
    for _ in range(5):
        app.processEvents()
    assert scroll.value() == saved


def test_startup_and_theme_switches_emit_no_invalid_font_warning(app, settings):
    messages = []
    previous = qInstallMessageHandler(lambda kind, context, message: messages.append(message))
    widget = None
    try:
        widget = SnapWordWindow(settings=settings)
        widget.show()
        for theme in ("dark", "light"):
            widget.apply_theme(theme)
            app.processEvents()
        assert not [message for message in messages if "Point size <= 0" in message]
    finally:
        qInstallMessageHandler(previous)
        if widget is not None:
            widget.hide()
            widget.deleteLater()
