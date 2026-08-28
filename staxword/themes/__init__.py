"""Theme manager for StaxWord — handles built-in and user-defined themes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Directory where user themes are stored
_USER_THEMES_DIR = Path.home() / ".config" / "staxoffice" / "StaxWord" / "themes"

# Semantic color keys for the theme editor
THEME_COLORS: dict[str, str] = {
    "workspace_bg": "#f0f2f5",
    "editor_bg": "#ffffff",
    "text_color": "#202124",
    "toolbar_bg": "#f8f9fa",
    "toolbar_border": "#dadce0",
    "menu_bg": "#f8f9fa",
    "menu_hover": "#e8eaed",
    "button_bg": "#f1f3f4",
    "button_hover": "#e8eaed",
    "button_active": "#d2e3fc",
    "accent": "#4aa3ff",
    "accent_text": "#1a73e8",
    "scrollbar_bg": "#f1f1f1",
    "scrollbar_handle": "#c1c1c1",
    "tab_active_bg": "#ffffff",
    "tab_inactive_bg": "#f1f3f4",
    "border_color": "#dadce0",
    "footer_bg": "#f8f9fa",
    "page_shadow": "#dadce0",
}


def _builtin_themes_dir() -> Path:
    return Path(__file__).resolve().parent


def _user_themes_dir() -> Path:
    _USER_THEMES_DIR.mkdir(parents=True, exist_ok=True)
    return _USER_THEMES_DIR


def list_themes() -> dict[str, dict[str, Any]]:
    """Return all available themes: ``{"name": {"builtin": bool, "path": str}}``."""
    themes: dict[str, dict[str, Any]] = {}

    # Built-in themes
    for f in _builtin_themes_dir().glob("*.qss"):
        themes[f.stem] = {"builtin": True, "path": str(f)}

    # User themes (JSON)
    for f in _user_themes_dir().glob("*.json"):
        if f.stem not in themes:
            themes[f.stem] = {"builtin": False, "path": str(f)}

    return themes


def load_theme_colors(name: str) -> dict[str, str] | None:
    """Load color overrides for a user theme. Returns None for built-in themes."""
    path = _user_themes_dir() / f"{name}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def save_theme_colors(name: str, colors: dict[str, str]) -> None:
    """Save a user theme as a JSON color map."""
    path = _user_themes_dir() / f"{name}.json"
    path.write_text(json.dumps(colors, indent=2), encoding="utf-8")


def delete_theme(name: str) -> bool:
    """Delete a user theme. Returns False if it's built-in or doesn't exist."""
    path = _user_themes_dir() / f"{name}.json"
    if path.exists():
        path.unlink()
        return True
    return False


def is_builtin(name: str) -> bool:
    return (_builtin_themes_dir() / f"{name}.qss").exists()


def generate_qss(base_theme: str, color_overrides: dict[str, str]) -> str:
    """Read the base QSS file and apply color overrides using CSS variables.

    The base QSS files must use ``{var_name}`` placeholders for colors
    that can be overridden.
    """
    qss_path = _builtin_themes_dir() / f"{base_theme}.qss"
    if not qss_path.exists():
        # Fallback: use light theme
        qss_path = _builtin_themes_dir() / "light.qss"

    qss = qss_path.read_text(encoding="utf-8")

    # Merge with defaults
    colors = dict(THEME_COLORS)
    colors.update(color_overrides)

    # Replace {var_name} placeholders
    for key, value in colors.items():
        qss = qss.replace(f"{{{key}}}", value)

    return qss


def apply_theme_to_widget(widget: Any, theme_name: str) -> None:
    """Apply a theme (built-in or user) to a widget."""
    user_colors = load_theme_colors(theme_name)
    if user_colors:
        # User theme: generate from base light + overrides
        base = user_colors.pop("_base", "light")
        qss = generate_qss(base, user_colors)
    elif is_builtin(theme_name):
        qss_path = _builtin_themes_dir() / f"{theme_name}.qss"
        qss = qss_path.read_text(encoding="utf-8")
    else:
        qss = ""

    widget.setStyleSheet(qss)
