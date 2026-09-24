"""Local-first settings for SnapWord.

SnapWord keeps its preferences and user themes inside a small JSON settings
file in a platform-appropriate ZFordDev config directory. No cloud, no accounts.
"""

from __future__ import annotations

import contextlib
import json
import os
import sys
from pathlib import Path
from typing import Any

SETTINGS_FILENAME = "settings.json"
DEFAULT_THEME = "light"


def _default_config_dir() -> Path:
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return Path(base) / "ZFordDev" / "SnapWord"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "ZFordDev" / "SnapWord"
    return Path.home() / ".config" / "ZFordDev" / "SnapWord"


def app_config_dir() -> Path:
    override = os.environ.get("SNAPWORD_CONFIG_DIR")
    base = Path(override) if override else _default_config_dir()
    base.mkdir(parents=True, exist_ok=True)
    return base


def settings_path() -> Path:
    return app_config_dir() / SETTINGS_FILENAME


def load_settings() -> dict[str, Any]:
    path = settings_path()
    if not path.exists():
        return {}
    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
        return settings if isinstance(settings, dict) else {}
    except Exception:
        return {}


def save_settings(settings: dict[str, Any]) -> None:
    path = settings_path()
    # Persistence is best-effort; never crash the app over a write failure.
    with contextlib.suppress(Exception):
        path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
