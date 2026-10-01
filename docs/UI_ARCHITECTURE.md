# SnapWord UI architecture

The default workspace combines a compact menu bar, two rows of writing tools,
and a centered page whose first line stays near the top. Advanced toolbars are
available through **View → Toolbars**.

## Arranging the workspace

- Drag the dotted handle at the start of a section to reorder it or float it.
- Drag a floating section back to a window edge to dock it. Its context menu
  also offers **Return to toolbar area**.
- **View → Toolbars** controls individual sections. Hidden toolbars retain their
  menu commands and keyboard shortcuts.
- **View → Files** opens the dockable file browser.
- The file browser shows its current folder path. Use **Up** to move to the parent
  folder; the button is disabled at the filesystem root. Opening a file from the
  tree keeps the current folder in view.
- **View → Reset Workspace Layout** restores default ordering, visibility and
  window geometry. Advanced sections return to their default hidden state.

Layout, dock visibility, floating positions, geometry and theme are saved on
an accepted application close. Cancelling close does not persist a new layout.
The versioned state lives in `workspace.ini` alongside `settings.json`, including
when `SNAPWORD_CONFIG_DIR` is set. Incompatible old layout state falls back to
the current default layout.

## Module responsibilities

| Module | Responsibility |
| --- | --- |
| `ui/window.py` | Compose components and connect application-level commands |
| `ui/actions.py` | Own shared actions and shortcuts |
| `ui/toolbar.py` | Register sections and apply default rows/visibility |
| `ui/toolbar_sections/*.py` | Each section's widgets, editor wiring and state sync |
| `ui/toolbar_sections/base.py` | Common native docking and section context menu |
| `ui/menubar.py` | Place shared commands in menus |
| `ui/workspace.py` | Top alignment, page sizing and outer document scrolling |
| `ui/documents.py` | Tab lifecycle, file dialogs, save/discard/cancel behavior |
| `ui/tabs.py` | Tab presentation, close controls and reorder signals |
| `ui/layout_state.py` | Save, restore and reset workspace state |
| `ui/panels.py` | Auxiliary dock construction |
| `ui/metrics.py` | Shared page dimensions |
| `themes/palettes.py` | Semantic light/dark colors |
| `themes/layout.qss.in` | Shared theme geometry and widget states |

To add a section, subclass `ToolbarSection` in its own module, register it in
`toolbar_sections.SECTIONS`, and optionally add its key to
`ToolbarManager.DEFAULT_ROWS`. Register actions through `command()` and reuse
those action objects in menus. Avoid registering duplicate commands, reparenting
widgets out of hidden toolbars, or manually detaching toolbars with window flags.

Custom themes use the same stylesheet as built-ins. Theme-editor color overrides
now affect the generated stylesheet directly.

## Validation

See [Contributing to SnapWord](CONTRIBUTING.md) for the test and lint commands,
including headless Qt setup. The UI regression tests cover actual toolbar handle
dragging, floating/restoring/redocking, visibility, reset order, document growth,
top alignment, action synchronization, tab identity, and failed saves.
