"""Theme editor dialog — lets users customize colors and save as new themes."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..themes import THEME_COLORS, list_themes, save_theme_colors

# Human-readable labels for each color key
_COLOR_LABELS: dict[str, str] = {
    "workspace_bg": "Workspace background",
    "editor_bg": "Editor / page background",
    "text_color": "Text color",
    "toolbar_bg": "Toolbar background",
    "toolbar_border": "Toolbar border",
    "menu_bg": "Menu background",
    "menu_hover": "Menu hover",
    "button_bg": "Button background",
    "button_hover": "Button hover",
    "button_active": "Button active / pressed",
    "accent": "Accent color",
    "accent_text": "Accent text color",
    "scrollbar_bg": "Scrollbar background",
    "scrollbar_handle": "Scrollbar handle",
    "tab_active_bg": "Active tab background",
    "tab_inactive_bg": "Inactive tab background",
    "border_color": "Border color",
    "footer_bg": "Footer background",
    "page_shadow": "Page shadow / border",
}

# Grouped layout for the color picker grid
_COLOR_GROUPS: dict[str, list[str]] = {
    "Backgrounds": [
        "workspace_bg", "editor_bg", "toolbar_bg", "menu_bg",
        "footer_bg", "tab_active_bg", "tab_inactive_bg",
    ],
    "Text & Accent": ["text_color", "accent", "accent_text"],
    "Borders": ["toolbar_border", "border_color", "page_shadow"],
    "Buttons & Controls": ["button_bg", "button_hover", "button_active"],
    "Scrollbar": ["scrollbar_bg", "scrollbar_handle"],
    "Menus": ["menu_hover"],
}


class _ColorButton(QPushButton):
    """A button that shows a color swatch and opens a color picker."""

    color_changed = Signal(str, str)  # key, hex_color

    def __init__(self, key: str, color: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.key = key
        self._color = color
        self.setFixedSize(36, 26)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._pick_color)
        self._update_style()

    def _update_style(self) -> None:
        self.setStyleSheet(
            f"QPushButton {{ background-color: {self._color}; border: 1px solid #999; border-radius: 4px; }}"
            "QPushButton:hover { border: 2px solid #4aa3ff; }"
        )
        self.setToolTip(self._color)

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(QColor(self._color), self, _COLOR_LABELS.get(self.key, self.key))
        if color.isValid():
            self._color = color.name()
            self._update_style()
            self.color_changed.emit(self.key, self._color)

    def get_color(self) -> str:
        return self._color

    def set_color(self, color: str) -> None:
        self._color = color
        self._update_style()


class ThemeEditorDialog(QDialog):
    """Dialog for creating or editing a custom theme."""

    theme_saved = Signal(str)  # theme_name

    def __init__(
        self,
        parent: QWidget | None = None,
        initial_name: str = "",
        initial_colors: dict[str, str] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Theme Editor")
        self.setMinimumSize(560, 520)

        self._color_buttons: dict[str, _ColorButton] = {}

        root = QVBoxLayout(self)

        # --- Theme name ---
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Theme name:"))
        self.name_input = QLineEdit(initial_name)
        self.name_input.setPlaceholderText("my-custom-theme")
        name_row.addWidget(self.name_input)
        root.addLayout(name_row)

        # --- Base theme ---
        base_row = QHBoxLayout()
        base_row.addWidget(QLabel("Base theme:"))
        self.base_combo = QComboBox()
        themes = list_themes()
        for name in sorted(themes):
            self.base_combo.addItem(name)
        self.base_combo.currentTextChanged.connect(self._on_base_changed)
        base_row.addWidget(self.base_combo)
        root.addLayout(base_row)

        # --- Color pickers (scrollable) ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        colors = initial_colors or dict(THEME_COLORS)

        for group_name, keys in _COLOR_GROUPS.items():
            group = QGroupBox(group_name)
            grid = QGridLayout(group)
            grid.setSpacing(8)

            for i, key in enumerate(keys):
                label = QLabel(_COLOR_LABELS.get(key, key))
                label.setFixedWidth(160)
                btn = _ColorButton(key, colors.get(key, THEME_COLORS.get(key, "#ffffff")))
                btn.color_changed.connect(self._on_color_changed)
                self._color_buttons[key] = btn

                row = i
                grid.addWidget(label, row, 0)
                grid.addWidget(btn, row, 1)

            scroll_layout.addWidget(group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        root.addWidget(scroll, 1)

        # --- Preview ---
        self._preview_label = QLabel()
        self._preview_label.setFixedHeight(40)
        self._update_preview()
        root.addWidget(self._preview_label)

        # --- Buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _on_color_changed(self, key: str, color: str) -> None:
        self._update_preview()

    def _on_base_changed(self, base: str) -> None:
        pass  # Base theme is just metadata; colors are independent

    def _update_preview(self) -> None:
        colors = self.get_colors()
        editor_bg = colors.get("editor_bg", "#ffffff")
        text_color = colors.get("text_color", "#202124")
        accent = colors.get("accent", "#4aa3ff")
        self._preview_label.setStyleSheet(
            f"background-color: {editor_bg}; color: {text_color}; "
            f"border: 2px solid {accent}; border-radius: 6px; padding: 8px;"
        )
        self._preview_label.setText("Preview — The quick brown fox jumps over the lazy dog")

    def get_colors(self) -> dict[str, str]:
        return {key: btn.get_color() for key, btn in self._color_buttons.items()}

    def get_theme_name(self) -> str:
        return self.name_input.text().strip()

    def get_base_theme(self) -> str:
        return self.base_combo.currentText()

    def _on_save(self) -> None:
        name = self.get_theme_name()
        if not name:
            self.name_input.setFocus()
            self.name_input.setStyleSheet("border: 2px solid red;")
            return

        colors = self.get_colors()
        colors["_base"] = self.get_base_theme()
        save_theme_colors(name, colors)
        self.theme_saved.emit(name)
        self.accept()
