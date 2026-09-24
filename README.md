# SnapWord (Otter) 🦦

A local-first word processor in the **Snap Ocean Suite** family.
Runs entirely on your machine — zero cloud, zero telemetry.

This is the **Otter** line — a Python/Qt reboot of StaxWord built with PySide6,
just as playful on documents as an otter. Rebranded and open-sourced under the
Snap ecosystem, with the cleanest successor format: **`.docs`**.

## Requirements

- Python 3.10 or later
- A desktop environment with a display server (or run headless with
  QT_QPA_PLATFORM=offscreen)

## Installation

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows
python -m pip install -e .
```

## Running

```
snapword                 # open a blank document
snapword file.docs       # open a document directly
snapword --version       # print version
```

## Features

- **Local-first, no account** — your documents stay on your drive, always.
- **Rich text editing** — fonts, colors, highlights, lists, alignment,
  indentation, line spacing, block quotes, and code blocks.
- **Insert everything** — links, images, tables, and horizontal rules anywhere
  in the document.
- **Multi-document tabs** — keep several documents open side by side.
- **Find & Replace** — quick search across the current document.
- **Light/dark themes** — plus user-editable themes.
- **Print & export PDF** — share documents without leaving the app.
- **`.docs` files** — the native SnapWord document format.

## Storage

Settings live in the SnapWord family config directory
(`%LOCALAPPDATA%\ZFordDev\SnapWord` on Windows,
`~/Library/Application Support/ZFordDev/SnapWord` on macOS,
`~/.config/ZFordDev/SnapWord` on Linux) inside `settings.json`.
The `SNAPWORD_CONFIG_DIR` environment variable overrides this location.

## Packaging

A standalone binary is produced with PyInstaller and published as a GitHub
Release asset on tagged builds:

```
python -m pip install -e ".[dev]" pyinstaller
pyinstaller --onefile --name snapword --add-data "snapword/themes/*;snapword/themes" snapword_launcher.py
```

## Development & tests

```
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
```

## Licence

MIT — see [LICENSE](LICENSE).