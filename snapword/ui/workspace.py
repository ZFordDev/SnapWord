"""Document presentation and outer scrolling, independent of window chrome."""

from PySide6.QtCore import QEvent, QPoint, Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

from .metrics import PAGE_WIDTH


class DocumentWorkspace(QScrollArea):
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.setObjectName("PageScrollArea")
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        workspace = QWidget()
        workspace.setObjectName("PageWorkspace")
        row = QHBoxLayout(workspace)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        self.page = QWidget()
        self.page.setObjectName("PageContainer")
        self.page.installEventFilter(self)
        self.page.setMaximumWidth(PAGE_WIDTH)
        page_layout = QVBoxLayout(self.page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)
        page_layout.addWidget(editor, 0, Qt.AlignTop)
        # Fixed-height editors otherwise get vertically centered in a tall page.
        page_layout.addStretch(1)
        row.addStretch(1)
        row.addWidget(self.page, 8)
        row.addStretch(1)
        self.setWidget(workspace)
        self._layout_timer = QTimer(self)
        self._layout_timer.setSingleShot(True)
        self._layout_timer.timeout.connect(self.update_page_height)
        self._scroll_target = None
        self._scroll_timer = QTimer(self)
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.timeout.connect(self._restore_scroll)
        editor.installEventFilter(self)
        editor.document().documentLayout().documentSizeChanged.connect(self.schedule_layout)
        editor.cursorPositionChanged.connect(self.ensure_cursor_visible)
        self.schedule_layout()

    def schedule_layout(self, *_):
        self._layout_timer.start(0)

    def eventFilter(self, watched, event):
        if watched is self.page and event.type() == QEvent.Type.MouseButtonPress:
            # The white page extends below the short QTextEdit on a new document.
            # Clicking that paper should focus the editor without jumping the caret.
            self.editor.setFocus(Qt.FocusReason.MouseFocusReason)
            return True
        if watched is self.editor and event.type() == QEvent.Type.Resize:
            self.schedule_layout()
        return super().eventFilter(watched, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.schedule_layout()

    def update_page_height(self):
        self.page.setMinimumHeight(max(self.viewport().height(), self.editor.height()))
        if self._scroll_target is not None:
            # Scroll ranges update after layout; applying this during tab load
            # would clamp a long document's saved position to the old range.
            self._scroll_timer.start(0)

    def restore_scroll(self, value):
        self._scroll_timer.stop()
        self._scroll_target = value
        self.schedule_layout()

    def _restore_scroll(self):
        if self._scroll_target is not None:
            expected = max(0, self.widget().height() - self.viewport().height())
            if (self.widget().height() < self.page.minimumHeight()
                    or self.verticalScrollBar().maximum() != expected):
                self._scroll_timer.start(0)
                return
            self.verticalScrollBar().setValue(self._scroll_target)
            self._scroll_target = None

    def ensure_cursor_visible(self):
        cursor = self.editor.cursorRect()
        position = self.editor.viewport().mapTo(self.widget(), QPoint(cursor.x(), cursor.y()))
        self.ensureVisible(position.x(), position.y(), 16, 40)
