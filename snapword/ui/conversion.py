"""Explicit consent for formats with known interchange limitations."""
from pathlib import Path

from PySide6.QtWidgets import QMessageBox


def confirm_conversion(parent, path, *, importing=False):
    suffix = Path(path).suffix.lower()
    if suffix in (".docx", ".odt"):
        detail = ("Basic text formatting, lists, links, images and tables are supported. "
                  "Advanced layout, merged/nested tables, complex numbering, comments, tracked changes, "
                  "headers and footers may not be preserved. Keep the original if you need these features.")
    elif suffix == ".rtf":
        detail = "RTF conversion is text-only. Formatting, images, links and tables will not be preserved."
    elif suffix in (".md", ".txt") and not importing:
        detail = ("Plain text does not preserve formatting or images." if suffix == ".txt" else
                  "Markdown preserves basic structure, but fonts, colors and advanced layout may be lost.")
    else:
        return True
    verb = "Open" if importing else "Save"
    reply = QMessageBox.warning(
        parent, f"{verb} with conversion limitations?", detail + "\n\nContinue?",
        QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel,
    )
    return reply == QMessageBox.Yes
