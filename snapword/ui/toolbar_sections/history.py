from .base import ToolbarSection


class HistorySection(ToolbarSection):
    key, title = "undo_redo", "History"

    def __init__(self, editor, actions, parent=None):
        super().__init__(editor, actions, parent)
        undo = self.command("edit.undo", "Undo", editor.undo, shortcut="Ctrl+Z")
        redo = self.command("edit.redo", "Redo", editor.redo, shortcut="Ctrl+Y")
        undo.setEnabled(editor.document().isUndoAvailable())
        redo.setEnabled(editor.document().isRedoAvailable())
        editor.undoAvailable.connect(undo.setEnabled)
        editor.redoAvailable.connect(redo.setEnabled)
