"""Application branding loaded relative to installed package resources."""
from pathlib import Path

from PySide6.QtGui import QIcon


def application_icon():
    # Qt's SVG renderer warns on the draft logo's filter primitives; use the
    # pre-rendered package icon at runtime and keep the SVG as its source.
    return QIcon(str(Path(__file__).with_name("assets") / "logo.png"))
