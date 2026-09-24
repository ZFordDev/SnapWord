# Changelog

## v0.1.0 (2026-09-25)

### Added

- Windows release builds now provide both a portable executable and a per-user
  installer. Linux and macOS releases provide their standalone executable files.
- Release workflow supports manual rehearsal, explicit publication, pre-release
  or stable metadata, and SHA-256 checksums. In-app updating remains deferred.

### Fixed

- Clicking the blank area of a document page now focuses the editor while keeping
  the caret at its previous position.
- Docked toolbar sections are restricted to the top toolbar band, and floating
  sections stay within an available screen area while being dragged.
- Added a visible dropdown arrow to toolbar formatting controls.
- Removed an SVG filter unsupported by Qt's SVG renderer; the app now loads the
  generated PNG icon at runtime to avoid the Windows startup warning.

### Docs

### Planned

#### Release-readiness review — 2026-09-24

Original findings are retained below, with fix-pass status appended. Checked
items have local regression evidence; unchecked items still need release validation.
P0 = release blocker, P1 = high priority, P2 = normal priority.

##### Document safety and format fidelity

- [x] **SW-001 · P0 — Prevent silent rich-document loss during import/save.**
  `snapword/formats.py` saves DOCX/ODT from plain text, and DOCX import only reads
  paragraph text/headings. A probe importing a bold paragraph plus a table lost
  both bold formatting and the table; saving a rich document produced no bold
  runs or tables. RTF and Markdown export also flatten formatting. Preserve
  supported structures and warn explicitly about unsupported/lossy conversion
  before overwriting documents. Verify formatted text, lists, links, images and
  tables with representative round-trip fixtures.
  **Fix-pass status:** Basic DOCX/ODT rich conversion and Markdown markup export now have regression fixtures; lossy formats require confirmation (Cancel by default). RTF remains explicitly text-only.

- [x] **SW-002 · P0 — Make inserted images permanent and portable.**
  `SnapWordEditor.insert_image_from_path()` inserts an absolute temporary-file
  reference; the probe's HTML pointed into the Windows Temp directory.
  `.docs`/HTML saving does not embed or copy that image. Moving a document to
  another computer or cleaning temporary files can break its images. Bundle or
  embed image data and verify reopening after the temporary source is removed.
  Include pasted images and every advertised image format in that check.
  **Fix-pass status:** Inserted/pasted images are embedded as PNG data URLs. Six advertised image types survive deletion of their source; relative HTML/Markdown images are embedded on import.

- [x] **SW-003 · P1 — Make document saves atomic.**
  Inspection of `save_document()` shows direct writes to the destination, with
  no temporary sibling file and atomic replacement. Error dialogs preserve the
  dirty flag but cannot recover an original already truncated by a failed write.
  Preserve the previous file on interrupted/failed saves; verify with injected
  write failures. This is a code-inspection finding, not a simulated power-loss test.
  **Fix-pass status:** Document and PDF writes use a temporary sibling and atomic replacement. Injected write failures leave the original file intact.

- [x] **SW-004 · P1 — Preserve ODT block order.**
  `_load_odt_as_html()` collects all paragraphs before all headings. A document
  with a heading followed by a paragraph imported as paragraph then heading.
  Traverse document content in order and test interleaved headings/paragraphs.
  **Fix-pass status:** ODT import traverses blocks in source order and ignores structural XML whitespace; an interleaved heading/paragraph fixture verifies ordering.

##### Editing and search

- [x] **SW-005 · P1 — Retain undo/redo history across tab switches.**
  `DocumentController.activate()` restores HTML into one editor; `setHtml()` clears
  its undo stack. The probe changed from undo available to unavailable after
  switching away and back. Maintain a document/undo history per tab and verify
  independent undo/redo after switching and reordering tabs.
  **Fix-pass status:** Each tab retains its QTextDocument and undo stack; switching tabs preserves independent histories.

- [x] **SW-006 · P2 — Derive dirty state from the saved document state.**
  `_on_text_changed()` only turns `_dirty` on. Typing and undoing back to the
  original blank document left `is_dirty()` true while Qt reported
  `document().isModified()` false. Synchronize dirty indicators and close prompts
  with save points, including undo/redo around saves.
  **Fix-pass status:** Dirty indicators follow Qt modification/save points. Undo to the saved state clears dirty; redo restores it.

- [x] **SW-007 · P1 — Make Ctrl+H reveal the Find & Replace bar.**
  `SnapWordWindow._open_find_replace()` calls `show_replace()`, which shows the
  child controls but never the hidden parent bar. Both remained invisible in the
  startup probe. Open Find & Replace directly from a fresh window and after closing it.
  **Fix-pass status:** Find & Replace explicitly reveals its parent bar; a window regression verifies the controls are visible.

- [x] **SW-008 · P1 — Stop match counting from destroying the search selection.**
  `FindReplaceBar._update_result_count()` moves the live editor cursor to the
  start, searches, then restores that already-modified cursor. After Find Next
  on `hello middle hello`, the selection was empty and the cursor was at zero.
  Count matches with an independent cursor and preserve selection/scroll position;
  verify next, previous and wraparound.
  **Fix-pass status:** Match counting uses a separate cursor; next/previous selection remains intact.

- [x] **SW-009 · P2 — Respect case-insensitive matching in Replace Current.**
  `replace_current()` compares the selection with an exact string equality even
  when Match Case is off. Searching `hello` with selected `HELLO` did not replace
  it. Use the same matching rules for finding and replacing, with tests for both modes.
  **Fix-pass status:** Replace Current honors the Match Case setting instead of requiring exact case in all modes.

- [x] **SW-010 · P2 — Insert link text/URLs without interpreting user input as HTML.**
  `insert_link()` interpolates both fields into HTML without escaping. Display text
  `<b>literal</b>` became formatted `literal` instead of the requested text.
  Escape the fields or use text/anchor formats; test angle brackets, quotes and ampersands.
  **Fix-pass status:** Links use QTextCharFormat anchors and literal inserted text; markup characters and quoted URLs are covered.

##### Settings and error feedback

- [x] **SW-011 · P1 — Validate settings before building the UI.**
  `load_settings()` accepts any valid JSON; `load_prefs()` assumes a dictionary.
  A temporary settings file containing `[1]` raised `TypeError`. Preference
  widgets also receive raw values without schema/type validation. Invalid shapes
  or field values should fall back to defaults without blocking startup/preferences.
  **Fix-pass status:** Settings shapes, types and ranges are validated before preference widgets are constructed; invalid JSON values fall back safely.

- [x] **SW-012 · P2 — Surface export failures in the GUI.**
  `SnapWordEditor.export_document()` catches errors and only prints to stdout;
  PDF export also has no visible success/failure verification. An unwritable export
  target can leave users without useful feedback. Add actionable UI errors and
  verify failed exports without marking the source document saved.
  **Fix-pass status:** Export failures show GUI errors and retain the source dirty state. A failed PDF export preserves an existing target.

##### Release pipeline and branding

- [x] **SW-013 · P0 — Use the working launcher in automated release builds.**
  `.github/workflows/release.yml` builds `snapword/main.py`, whose package-relative
  imports fail when used as a standalone script. Running that entry point produced
  `ImportError: attempted relative import with no known parent package`.
  The local spec already uses `snapword_launcher.py`; align the workflow and
  verify the actual frozen application starts. A frozen release build was not run
  during this review.
  **Fix-pass status:** The release workflow builds the launcher-based spec; the resulting Windows executable passes version and UI-startup smoke checks.

- [x] **SW-014 · P1 — Make release verification fail on broken binaries.**
  The release smoke test ends with `--version || true`, masking all failures;
  `--version` alone does not construct the editor UI. Remove failure suppression
  and add a bounded application-startup check before uploading release assets.
  **Fix-pass status:** Binary checks propagate failures and apply a 60-second timeout to version/startup checks; failure propagation has a regression test.

- [x] **SW-015 · P1 — Run the full regression suite in CI.**
  CI uses `unittest discover`, which skips the 17 pytest function tests in
  `tests/test_ui_workspace.py`, including docking, persistence and save-failure
  coverage. Switch the CI test command to pytest and verify those cases are collected.
  Update the README development test command to match.
  **Fix-pass status:** CI/release tests now use pytest, collecting both unittest and pytest cases; README commands match.

- [ ] **SW-016 · P1 — Give platform release artifacts distinct names.**
  Linux and macOS jobs both upload a file named `snapword` to the same release.
  The workflow has no platform-specific archive/name, creating an asset collision.
  Publish distinct OS/architecture artifacts and verify every matrix output remains
  available. This is a workflow-inspection finding; no release was published.
  **Fix-pass status:** Implemented OS/architecture-specific standalone asset names. Windows additionally builds an installer; Linux/macOS ship one executable each. Manual rehearsal and tag publication are separate workflow paths, and assets receive SHA-256 checksums. Cross-platform Actions builds remain to be exercised.

- [ ] **SW-017 · P2 — Integrate and package the draft application logo.**
  `snapword/assets/logo.svg` parses and renders successfully at 512×512, but
  `windowIcon().isNull()` is true. There is no app-icon setup, asset package-data
  rule, PyInstaller asset inclusion or executable icon configuration. Keep the
  draft SVG as the source, prepare platform icon variants, wire application/window
  icons, and verify installed/frozen builds plus 16/32/48-pixel legibility on both themes.
  **Fix-pass status:** Application/window icons, package assets, generated ICO/ICNS/PNG and executable icon configuration are implemented. Windows frozen startup loads the icon. Removed the SVG filter that triggered Qt's renderer warning and switched the runtime icon to PNG. Native 16/32/48-pixel light/dark visual review and macOS/Linux installed/frozen checks remain open.

#### Review baseline

- Existing automated suite: **95 passed** using the offscreen Qt platform.
- Lint: `ruff check snapword tests` passed.
- Additional isolated probes reproduced the document, editing, settings and
  entry-point findings above using temporary files/configuration.
- The logo was inspected via Qt SVG rendering; its visual design remains a draft.
- No application fixes were made in this review pass. Manual native-platform
  release testing and actual frozen build verification remain outstanding.

#### Fix-pass verification — 2026-09-25

- Windows offscreen regression suite: **127 passed** (one pre-existing deprecated
  Qt test API warning). `ruff check .` passed.
- Windows PyInstaller executable built with the spec and passed version/UI startup checks.
- Source wheel built with packaged branding assets; generated platform icons retain the draft SVG.
- No release was published. macOS/Linux binaries, matrix asset uploads and native
  icon legibility remain release-gate checks (SW-016/SW-017).
- Atomic-save tests simulate write failure, not power loss. DOCX/ODT support is
  basic interchange, not full Microsoft Word layout fidelity; keep source originals.
- Pre-packaging UI niceties were addressed after this fix pass: clicking page
  whitespace restores editor focus at the existing caret; floating toolbars are
  screen-clamped; toolbar combos show dropdown arrows; the runtime uses a
  renderer-compatible PNG icon. These latest UI changes have not been manually
  exercised yet.
