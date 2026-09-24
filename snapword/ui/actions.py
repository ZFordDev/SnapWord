"""Shared commands: a single QAction per command, regardless of placement."""

from PySide6.QtCore import QObject
from PySide6.QtGui import QAction, QKeySequence


class ActionRegistry(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._actions = {}

    def add(self, key, label, callback=None, *, shortcut=None, checkable=False, icon_text=None):
        if key in self._actions:
            raise ValueError(f"Duplicate command: {key}")
        action = QAction(label, self)
        action.setObjectName(key)
        action.setCheckable(checkable)
        if icon_text:
            action.setIconText(icon_text)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.setToolTip(label + (f" ({action.shortcut().toString()})" if shortcut else ""))
        if callback:
            action.triggered.connect(callback)
        self._actions[key] = action
        # Shortcuts remain available even when their toolbar is hidden.
        if self.parent() is not None:
            self.parent().addAction(action)
        return action

    def __getitem__(self, key):
        return self._actions[key]
