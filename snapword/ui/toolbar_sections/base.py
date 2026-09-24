"""Common native docking behavior for real toolbar sections."""

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMenu, QToolBar


class ToolbarSection(QToolBar):
    key = ""
    title = ""

    def __init__(self, editor, actions, parent=None):
        super().__init__(self.title, parent)
        self.editor = editor
        self.registry = actions
        self.setObjectName(f"Toolbar_{self.key}")
        self.setMovable(True)
        self.setFloatable(True)
        self.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        self._clamping_floating_position = False
        self.setToolTip(f"{self.title}: drag the dotted handle to move or undock; right-click to return")
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)

    def moveEvent(self, event):
        super().moveEvent(event)
        if not self.isFloating() or self._clamping_floating_position:
            return
        frame = self.frameGeometry()
        screens = QGuiApplication.screens()
        if not screens:
            return
        screen = QGuiApplication.screenAt(frame.center())
        if screen is None:
            def distance(candidate):
                area = candidate.availableGeometry()
                dx = max(area.left() - frame.center().x(), 0, frame.center().x() - area.right())
                dy = max(area.top() - frame.center().y(), 0, frame.center().y() - area.bottom())
                return dx * dx + dy * dy

            screen = min(screens, key=distance)
        area = screen.availableGeometry()
        x = min(max(frame.left(), area.left()), max(area.left(), area.right() - frame.width() + 1))
        y = min(max(frame.top(), area.top()), max(area.top(), area.bottom() - frame.height() + 1))
        if (x, y) != (frame.left(), frame.top()):
            self._clamping_floating_position = True
            try:
                self.move(self.pos() + QPoint(x - frame.left(), y - frame.top()))
            finally:
                self._clamping_floating_position = False

    def command(self, key, label, callback, **options):
        action = self.registry.add(key, label, callback, **options)
        self.addAction(action)
        button = self.widgetForAction(action)
        if button is not None:
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            # Keep labels readable; let Qt's extension button handle overflow.
            button.setMinimumWidth(button.sizeHint().width())
        return action

    def _context_menu(self, position):
        menu = QMenu(self)
        dock = menu.addAction("Return to toolbar area")
        dock.triggered.connect(self.dock)
        menu.addAction(self.toggleViewAction())
        menu.exec(self.mapToGlobal(position))

    def dock(self):
        # Reinsert through QMainWindow; retain ownership and native docking.
        window = self.parentWidget()
        window.removeToolBar(self)
        window.addToolBar(Qt.ToolBarArea.TopToolBarArea, self)
        self.show()
