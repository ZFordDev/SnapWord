# Contributing to SnapWord

Thanks for helping Otter swim in the right direction. This page collects the
developer and release details that do not belong in the main user README.

## Development setup

Create a virtual environment and install the development dependencies:

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
```

Run the full test suite and lint checks:

```bash
python -m pytest -q
python -m ruff check snapword tests
```

The UI tests use temporary settings when they need to inspect workspace layout.

## Headless Qt testing

On a machine without a desktop display, run Qt in offscreen mode. PowerShell:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
$env:SNAPWORD_CONFIG_DIR = Join-Path $env:TEMP 'snapword-tests'
python -m pytest -q
```

On macOS and Linux, the equivalent shell setup is:

```bash
export QT_QPA_PLATFORM=offscreen
export SNAPWORD_CONFIG_DIR="$(mktemp -d)/snapword-tests"
python -m pytest -q
```

Headless rendering may need an explicitly registered font when the machine has
no system font database.

## UI architecture

See [UI architecture and workspace customization](UI_ARCHITECTURE.md) for
toolbar ownership, layout persistence, theme styling, and UI regression details.

## Building a release

Install the build dependencies:

```bash
python -m pip install -e ".[dev,build]"
```

Build and check the application:

```bash
python scripts/build_icons.py
pyinstaller --noconfirm snapword.spec
python scripts/check_binary.py dist/snapword.exe
python scripts/package_release.py v0.1.0
```

Use `dist/snapword` for the binary check on Linux and macOS. On Windows, build
the per-user installer with Inno Setup:

```powershell
iscc /DAppVersion=0.1.0 /Odist-release installer/snapword.iss
```

GitHub Actions rehearses manual release runs by default. Tagged releases publish
platform assets and checksums according to the workflow configuration.
