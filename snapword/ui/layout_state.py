"""Versioned workspace persistence, restored only after all docks exist."""

from PySide6.QtCore import QByteArray, QSettings

from ..config import app_config_dir


class WorkspaceLayout:
    VERSION = 2

    def __init__(self, window, toolbars, file_dock, settings=None):
        self.window = window
        self.toolbars = toolbars
        self.file_dock = file_dock
        self.settings = (
            settings
            if settings is not None
            else QSettings(str(app_config_dir() / "workspace.ini"), QSettings.Format.IniFormat)
        )
        self.default_geometry = window.saveGeometry()
        self.default_state = window.saveState(self.VERSION)

    def restore(self):
        geometry = self.settings.value("window_geometry")
        if isinstance(geometry, QByteArray) and geometry:
            self.window.restoreGeometry(geometry)
        state = self.settings.value("toolbar_layout")
        if isinstance(state, QByteArray) and state and not self.window.restoreState(state, self.VERSION):
            self.window.restoreState(self.default_state, self.VERSION)

    def save(self):
        self.settings.setValue("toolbar_layout", self.window.saveState(self.VERSION))
        self.settings.setValue("window_geometry", self.window.saveGeometry())
        self.settings.setValue("theme", self.window._current_theme)
        self.settings.sync()

    def reset(self):
        self.window.restoreGeometry(self.default_geometry)
        self.window.restoreState(self.default_state, self.VERSION)
        self.toolbars.reset()
        self.file_dock.hide()
        self.settings.remove("toolbar_layout")
        self.settings.remove("window_geometry")
