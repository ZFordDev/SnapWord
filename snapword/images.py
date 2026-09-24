"""Self-contained image resources for HTML-backed documents."""
import base64
import re
from html import escape, unescape
from pathlib import Path

from PySide6.QtCore import QBuffer, QIODevice, QUrl
from PySide6.QtGui import QImage


def image_data_url(image):
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    if image.isNull() or not image.save(buffer, "PNG"):
        raise ValueError("Could not encode the image as PNG.")
    return "data:image/png;base64," + base64.b64encode(bytes(buffer.data())).decode("ascii")


def portable_html(html, base=None):
    """Embed local images; reject unresolved resources before saving a document."""
    def replace(match):
        source = unescape(match.group(2))
        if source.startswith("data:image/"):
            return match.group(0)
        url = QUrl(source)
        if url.isLocalFile():
            path = Path(url.toLocalFile())
        elif re.match(r"^[A-Za-z]:[\\/]", source) or not url.scheme():
            path = Path(source)
            if not path.is_absolute() and base:
                path = Path(base) / path
        else:
            raise ValueError(f"Image is not embedded: {source}. Insert a local copy before saving.")
        image = QImage(str(path))
        if image.isNull():
            raise ValueError(f"Image is missing or unreadable: {path}")
        return match.group(1) + '"' + escape(image_data_url(image), quote=True) + '"'

    return re.sub(r'''(<img\b[^>]*?\bsrc\s*=\s*)["']([^"']*)["']''', replace, html, flags=re.IGNORECASE)
