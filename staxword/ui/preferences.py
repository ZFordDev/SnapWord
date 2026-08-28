"""Preferences dialog for StaxWord — font sizes, default settings."""

import contextlib
import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

_PREFS_PATH = Path.home() / ".config" / "staxoffice" / "StaxWord" / "prefs.json"

_DEFAULTS: dict[str, Any] = {
    "editor_font_family": "Arial",
    "editor_font_size": 12,
    "toolbar_font_size": 13,
    "sidebar_font_size": 13,
    "footer_font_size": 11,
    "line_spacing": 1.5,
    "tab_width": 4,
    "recent_files": [],
}


def load_prefs() -> dict[str, Any]:
    """Load user preferences, falling back to defaults."""
    prefs = dict(_DEFAULTS)
    if _PREFS_PATH.exists():
        with contextlib.suppress(Exception):
            prefs.update(json.loads(_PREFS_PATH.read_text(encoding="utf-8")))
    return prefs


def save_prefs(prefs: dict[str, Any]) -> None:
    """Save user preferences to disk."""
    _PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Don't persist recent_files list in this save
    to_save = {k: v for k, v in prefs.items() if k != "recent_files"}
    _PREFS_PATH.write_text(json.dumps(to_save, indent=2), encoding="utf-8")


def get_pref(key: str) -> Any:
    return load_prefs().get(key, _DEFAULTS.get(key))


class PreferencesDialog(QDialog):
    """Preferences dialog with font sizes and editor settings."""

    prefs_changed = Signal(dict)  # emits updated prefs

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setMinimumWidth(420)

        self._prefs = load_prefs()

        root = QVBoxLayout(self)

        # --- Editor group ---
        editor_group = QGroupBox("Editor")
        editor_form = QFormLayout(editor_group)

        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems(["Arial", "Calibri", "Times New Roman", "Georgia", "Verdana", "Courier New"])
        self.font_family_combo.setCurrentText(self._prefs.get("editor_font_family", "Arial"))
        editor_form.addRow("Font family:", self.font_family_combo)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(self._prefs.get("editor_font_size", 12))
        self.font_size_spin.setSuffix("pt")
        editor_form.addRow("Font size:", self.font_size_spin)

        self.line_spacing_spin = QComboBox()
        for val in ["1.0", "1.15", "1.5", "2.0"]:
            self.line_spacing_spin.addItem(val, float(val))
        idx = self.line_spacing_spin.findData(self._prefs.get("line_spacing", 1.5))
        if idx >= 0:
            self.line_spacing_spin.setCurrentIndex(idx)
        editor_form.addRow("Line spacing:", self.line_spacing_spin)

        root.addWidget(editor_group)

        # --- UI group ---
        ui_group = QGroupBox("Interface")
        ui_form = QFormLayout(ui_group)

        self.toolbar_font_spin = QSpinBox()
        self.toolbar_font_spin.setRange(8, 24)
        self.toolbar_font_spin.setValue(self._prefs.get("toolbar_font_size", 13))
        self.toolbar_font_spin.setSuffix("px")
        ui_form.addRow("Toolbar font size:", self.toolbar_font_spin)

        self.sidebar_font_spin = QSpinBox()
        self.sidebar_font_spin.setRange(8, 24)
        self.sidebar_font_spin.setValue(self._prefs.get("sidebar_font_size", 13))
        self.sidebar_font_spin.setSuffix("px")
        ui_form.addRow("Sidebar font size:", self.sidebar_font_spin)

        self.footer_font_spin = QSpinBox()
        self.footer_font_spin.setRange(8, 24)
        self.footer_font_spin.setValue(self._prefs.get("footer_font_size", 11))
        self.footer_font_spin.setSuffix("px")
        ui_form.addRow("Footer font size:", self.footer_font_spin)

        root.addWidget(ui_group)

        # --- Buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _on_ok(self) -> None:
        self._prefs["editor_font_family"] = self.font_family_combo.currentText()
        self._prefs["editor_font_size"] = self.font_size_spin.value()
        self._prefs["line_spacing"] = float(self.line_spacing_spin.currentText())
        self._prefs["toolbar_font_size"] = self.toolbar_font_spin.value()
        self._prefs["sidebar_font_size"] = self.sidebar_font_spin.value()
        self._prefs["footer_font_size"] = self.footer_font_spin.value()
        save_prefs(self._prefs)
        self.prefs_changed.emit(self._prefs)
        self.accept()
