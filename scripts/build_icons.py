"""Render platform icon assets from the unchanged draft SVG."""
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication


def main():
    app = QApplication.instance() or QApplication([])
    assets = Path(__file__).resolve().parents[1] / "snapword" / "assets"
    renderer = QSvgRenderer(str(assets / "logo.svg"))
    if not renderer.isValid():
        raise ValueError("Invalid logo SVG")
    canvas = QImage(1024, 1024, QImage.Format_ARGB32)
    canvas.fill(Qt.transparent)
    painter = QPainter(canvas)
    renderer.render(painter)
    painter.end()
    canvas.save(str(assets / "logo.png"))
    with Image.open(assets / "logo.png") as image:
        image.save(assets / "logo.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
        image.save(assets / "logo.icns", format="ICNS")
    app.processEvents()


if __name__ == "__main__":
    main()
