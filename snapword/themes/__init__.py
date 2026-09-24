"""Theme persistence and one shared stylesheet for all palettes."""

import json
import re
from pathlib import Path

from PySide6.QtGui import QColor

from ..config import app_config_dir
from ..ui.metrics import PAGE_HORIZONTAL_PADDING, PAGE_VERTICAL_PADDING
from .palettes import LIGHT, PALETTES

_USER_THEMES_DIR = app_config_dir() / "themes"
THEME_COLORS = dict(LIGHT)
_TEMPLATE = Path(__file__).with_name("layout.qss.in")


def _theme_path(name):
    if not isinstance(name, str) or not re.fullmatch(r"[\w .-]+", name) or name in (".", ".."):
        raise ValueError("Use letters, numbers, spaces, dots, underscores or hyphens in theme names.")
    return _USER_THEMES_DIR / f"{name}.json"


def _user_themes_dir():
    _USER_THEMES_DIR.mkdir(parents=True, exist_ok=True)
    return _USER_THEMES_DIR


def list_themes():
    themes = {name: {"builtin": True, "path": str(_TEMPLATE)} for name in PALETTES}
    for path in _user_themes_dir().glob("*.json"):
        if path.stem not in themes:
            themes[path.stem] = {"builtin": False, "path": str(path)}
    return themes


def load_theme_colors(name):
    try:
        path = _theme_path(name)
        if path.exists():
            colors = json.loads(path.read_text(encoding="utf-8"))
            return colors if isinstance(colors, dict) else None
    except (OSError, ValueError):
        pass
    return None


def save_theme_colors(name, colors):
    if is_builtin(name):
        raise ValueError("Choose a new name for your custom theme.")
    path = _theme_path(name)
    _user_themes_dir()
    path.write_text(json.dumps(colors, indent=2), encoding="utf-8")


def delete_theme(name):
    if is_builtin(name):
        return False
    path = _theme_path(name)
    if path.exists():
        path.unlink()
        return True
    return False


def is_builtin(name):
    return name in PALETTES


def resolved_colors(name):
    if name in PALETTES:
        return dict(PALETTES[name])
    overrides = load_theme_colors(name) or {}
    colors = dict(PALETTES.get(overrides.get("_base"), LIGHT))
    for key, value in overrides.items():
        if key in colors and isinstance(value, str) and QColor(value).isValid():
            colors[key] = value
    return colors


def generate_qss(base_theme, color_overrides):
    colors = resolved_colors(base_theme)
    for key, value in color_overrides.items():
        if key in colors and isinstance(value, str) and QColor(value).isValid():
            colors[key] = value
    values = {
        **colors,
        "page_vertical_padding": PAGE_VERTICAL_PADDING,
        "page_horizontal_padding": PAGE_HORIZONTAL_PADDING,
    }
    qss = _TEMPLATE.read_text(encoding="utf-8")
    for key, value in values.items():
        qss = qss.replace("{" + key + "}", str(value))
    return qss


def apply_theme_to_widget(widget, theme_name):
    widget.setStyleSheet(generate_qss(theme_name, {}))
