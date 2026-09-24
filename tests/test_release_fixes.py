"""Reproductions for the release checklist, promoted to regression tests."""

import base64
import runpy
import subprocess
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtCore import QMimeData, QSettings, QUrl
from PySide6.QtGui import QFontDatabase, QImage, QTextDocument
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from snapword.formats import load_as_html, save_document
from snapword.images import image_data_url
from snapword.ui.conversion import confirm_conversion
from snapword.ui.editor import SnapWordEditor
from snapword.ui.preferences import PreferencesDialog, load_prefs
from snapword.ui.window import SnapWordWindow


@pytest.fixture
def app():
    application = QApplication.instance() or QApplication([])
    if not QFontDatabase.families():
        for font in ("C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
            if Path(font).exists():
                QFontDatabase.addApplicationFont(font)
                break
    return application


@pytest.fixture
def window(app, tmp_path):
    widget = SnapWordWindow(settings=QSettings(str(tmp_path / "layout.ini"), QSettings.IniFormat))
    widget.show()
    app.processEvents()
    yield widget
    widget.hide()
    widget.deleteLater()
    app.processEvents()


@pytest.fixture
def rich_html(app):
    image = QImage(8, 8, QImage.Format_ARGB32)
    image.fill(0xFFB943A6)
    return (
        "<h1>Title</h1><p><b>Bold</b> <i>Italic</i> "
        '<a href="https://example.com?a=1&amp;b=2">Link</a></p>'
        '<ul><li>Bullet</li></ul><table border="1"><tr><td>Cell</td></tr></table>'
        f'<p><img src="{image_data_url(image)}" width="8" height="8"></p>'
    )


@pytest.mark.parametrize("suffix", [".docs", ".docx", ".odt"])
def test_rich_roundtrip(app, tmp_path, rich_html, suffix):
    destination = tmp_path / ("rich" + suffix)
    save_document(str(destination), rich_html, "plain fallback must not be used")
    html = load_as_html(str(destination))
    doc = QTextDocument()
    doc.setHtml(html)
    assert "Title" in doc.toPlainText()
    assert "Cell" in doc.toPlainText()
    assert "<table" in html
    assert "data:image/" in html
    assert doc.find("Bold").charFormat().fontWeight() >= 700
    assert doc.find("Italic").charFormat().fontItalic()
    assert doc.find("Link").charFormat().anchorHref() == "https://example.com?a=1&b=2"
    assert doc.find("Bullet").block().textList() is not None


def test_markdown_export_preserves_basic_markup(app, tmp_path):
    path = tmp_path / "content.md"
    save_document(str(path), "<h1>Heading</h1><p><b>Bold</b></p>", "Heading\nBold")
    output = path.read_text(encoding="utf-8")
    assert "# Heading" in output and "**Bold**" in output


def test_rtf_unicode_roundtrip(app, tmp_path):
    text = "Café 中文 🦦 {literal}"
    path = tmp_path / "unicode.rtf"
    save_document(str(path), "", text)
    document = QTextDocument()
    document.setHtml(load_as_html(str(path)))
    assert document.toPlainText() == text


def test_odt_interleaved_block_order(app, tmp_path):
    path = tmp_path / "ordered.odt"
    from snapword.odt_format import NS

    namespaces = " ".join(f'xmlns:{key}="{value}"' for key, value in NS.items())
    content = (
        f"<office:document-content {namespaces}><office:body><office:text>\n"
        '<text:h text:outline-level="1">First</text:h>\n<text:p>Second</text:p>\n'
        '<text:h text:outline-level="2">Third</text:h>\n<text:p>Fourth</text:p>\n'
        "</office:text></office:body></office:document-content>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("content.xml", content)
    document = QTextDocument()
    document.setHtml(load_as_html(str(path)))
    assert document.toPlainText().splitlines() == ["First", "Second", "Third", "Fourth"]


def test_markdown_relative_images_are_embedded(app, tmp_path):
    image = QImage(8, 8, QImage.Format_RGB32)
    image.fill(0xFFFFFFFF)
    assert image.save(str(tmp_path / "image.png"))
    path = tmp_path / "image.md"
    path.write_text("![Image](image.png)", encoding="utf-8")
    assert "data:image/png;base64," in load_as_html(str(path))


def test_lossy_save_requires_explicit_confirmation(window, tmp_path):
    window.editor.insertPlainText("unsaved")
    target = tmp_path / "original.docx"
    target.write_bytes(b"original")
    with (
        patch.object(QFileDialog, "getSaveFileName", return_value=(str(target), "Microsoft Word")),
        patch.object(QMessageBox, "warning", return_value=QMessageBox.Cancel),
    ):
        assert not window.documents.save_as()
    assert target.read_bytes() == b"original"
    assert window.editor.is_dirty()


def test_conversion_warning_covers_limited_formats(window):
    with patch.object(QMessageBox, "warning", return_value=QMessageBox.Cancel) as warning:
        for suffix in ("docx", "odt", "rtf", "md", "txt"):
            assert not confirm_conversion(window, "file." + suffix)
        assert warning.call_count == 5


def test_failed_write_keeps_original(app, tmp_path):
    path = tmp_path / "document.docs"
    path.write_text("original", encoding="utf-8")

    def fail(destination, *_):
        Path(destination).write_text("partial", encoding="utf-8")
        raise OSError("disk full")

    with patch("snapword.formats._write_document", side_effect=fail), pytest.raises(OSError):
        save_document(str(path), "<p>replacement</p>", "replacement")
    assert path.read_text(encoding="utf-8") == "original"
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("extension", ["png", "jpg", "bmp", "webp", "gif", "svg"])
def test_images_survive_source_removal(app, tmp_path, extension):
    source = tmp_path / ("image." + extension)
    if extension == "gif":
        source.write_bytes(base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"))
    elif extension == "svg":
        source.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8">'
            '<rect width="8" height="8" fill="red"/></svg>',
            encoding="utf-8",
        )
    else:
        image = QImage(8, 8, QImage.Format_RGB32)
        image.fill(0xFFB943A6)
        assert image.save(str(source))
    editor = SnapWordEditor()
    editor.insert_image_from_path(str(source))
    html = editor.toHtml()
    assert "data:image/png;base64," in html
    source.unlink()
    saved = tmp_path / "portable.docs"
    save_document(str(saved), html, "")
    doc = QTextDocument()
    doc.setHtml(load_as_html(str(saved)))
    block = doc.begin()
    fragment = block.begin().fragment()
    name = fragment.charFormat().toImageFormat().name()
    assert not doc.resource(QTextDocument.ImageResource, QUrl(name)).isNull()


def test_pasted_image_is_embedded(app):
    editor = SnapWordEditor()
    mime = QMimeData()
    image = QImage(8, 8, QImage.Format_RGB32)
    image.fill(0xFFFFFFFF)
    mime.setImageData(image)
    editor.insertFromMimeData(mime)
    assert "data:image/png;base64," in editor.toHtml()


def test_undo_and_save_points_survive_switching(window, tmp_path):
    editor = window.editor
    editor.insertPlainText("first")
    with patch.object(QFileDialog, "getSaveFileName", return_value=(str(tmp_path / "saved.docs"), "")):
        assert window.documents.save()
    editor.insertPlainText(" more")
    assert editor.is_dirty()
    window.documents.new()
    editor.insertPlainText("second")
    window.tab_bar.set_current_index(0)
    editor.undo()
    assert editor.toPlainText() == "first"
    assert not editor.is_dirty()
    editor.redo()
    assert editor.is_dirty()
    window.tab_bar.set_current_index(1)
    editor.undo()
    assert editor.toPlainText() == ""
    assert not editor.is_dirty()


def test_search_and_replace_controls(window):
    window.editor.setPlainText("Hello middle hello")
    window._open_find_replace()
    bar = window.find_bar
    assert bar.isVisible() and bar.replace_widget.isVisible()
    bar.search_input.setText("hello")
    bar.find_next()
    assert window.editor.textCursor().selectedText() == "Hello"
    bar.find_next()
    assert window.editor.textCursor().selectedText() == "hello"
    bar.find_prev()
    assert window.editor.textCursor().selectedText() == "Hello"
    bar.replace_input.setText("bye")
    bar.replace_current()
    assert window.editor.toPlainText() == "bye middle hello"


def test_link_fields_are_literal(app):
    editor = SnapWordEditor()
    url = 'https://example.com/?x="quoted"&y=2'
    editor.insert_link(url, "<b>A & B</b>")
    assert editor.toPlainText() == "<b>A & B</b>"
    assert editor.document().find("A & B").charFormat().anchorHref() == url


@pytest.mark.parametrize(
    "content",
    [
        "[1]",
        "null",
        "42",
        '{"editor_font_size": "oops", "line_spacing": []}',
        '{"sidebar_font_size": null, "footer_font_size": -1}',
    ],
)
def test_invalid_settings_fall_back(app, tmp_path, monkeypatch, content):
    monkeypatch.setenv("SNAPWORD_CONFIG_DIR", str(tmp_path))
    (tmp_path / "settings.json").write_text(content, encoding="utf-8")
    prefs = load_prefs()
    assert isinstance(prefs["editor_font_size"], int)
    dialog = PreferencesDialog()
    assert dialog.font_size_spin.value() > 0


def test_export_failure_is_visible_and_not_saved(window, tmp_path):
    window.editor.insertPlainText("dirty")
    with (
        patch("snapword.ui.editor.save_document", side_effect=OSError("disk full")),
        patch.object(QMessageBox, "warning") as warning,
    ):
        assert not window.editor.export_document(str(tmp_path / "out.docs"))
        assert "disk full" in warning.call_args.args[2]
    assert window.editor.is_dirty()


def test_pdf_failure_is_visible_and_preserves_existing_file(window, tmp_path):
    target = tmp_path / "out.pdf"
    target.write_bytes(b"original")
    window.editor.insertPlainText("dirty")
    with (
        patch.object(QFileDialog, "getSaveFileName", return_value=(str(target), "")),
        patch.object(QTextDocument, "print_", side_effect=OSError("printer failed")),
        patch.object(QMessageBox, "warning") as warning,
    ):
        window.editor.export_pdf()
        assert "printer failed" in warning.call_args.args[2]
    assert target.read_bytes() == b"original"
    assert window.editor.is_dirty()


def test_application_icon_has_small_variants(window):
    assert not window.windowIcon().isNull()
    for size in (16, 32, 48):
        assert not window.windowIcon().pixmap(size, size).isNull()


@pytest.mark.parametrize("system", ["Windows", "Linux", "Darwin"])
def test_release_binary_is_platform_specific(tmp_path, monkeypatch, system):
    script = Path(__file__).resolve().parents[1] / "scripts" / "package_release.py"
    monkeypatch.chdir(tmp_path)
    distribution = tmp_path / "dist"
    distribution.mkdir()
    binary = "snapword.exe" if system == "Windows" else "snapword"
    (distribution / binary).write_bytes(b"fixture executable")
    monkeypatch.setattr(sys, "argv", [str(script), "v0.1.0"])
    with patch("platform.system", return_value=system), patch("platform.machine", return_value="arm64"):
        runpy.run_path(str(script), run_name="__main__")
    asset_system = "macos" if system == "Darwin" else system.lower()
    suffix = ".exe" if system == "Windows" else ""
    asset = tmp_path / f"dist-release/snapword-v0.1.0-{asset_system}-arm64{suffix}"
    assert asset.read_bytes() == b"fixture executable"


def test_binary_check_does_not_mask_failure(monkeypatch):
    script = Path(__file__).resolve().parents[1] / "scripts" / "check_binary.py"
    monkeypatch.setattr(sys, "argv", [str(script), "broken-binary"])
    with (
        patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "broken-binary")) as run,
        pytest.raises(subprocess.CalledProcessError),
    ):
        runpy.run_path(str(script), run_name="__main__")
    assert run.call_args.kwargs["check"] is True
    assert run.call_args.kwargs["timeout"] <= 60
