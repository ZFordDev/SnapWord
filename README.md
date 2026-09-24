<div align="center">

# SnapWord

### 🦦 Otter 🦦

**A local-first word processor that just wants to write.**

No accounts. No cloud dependency. No telemetry.
Just your documents, sitting exactly where you left them.

</div>

---

## 💡 What is SnapWord?

Sometimes you need more than a text editor.

Sometimes you also don't need an office suite trying to become your operating system.

**SnapWord** is a lightweight, local-first word processor built for normal documents: formatted text, images, tables, lists, links, printing, PDFs, and the other things you'd expect — without requiring an account or sending your documents somewhere else.

Your files are yours.

Your computer is the cloud.

The otter is just here to help. 🦦

---

## 🌊 Meet Otter

This is the **Otter** line of SnapWord — a Python + Qt reboot of the original **StaxWord**, rebuilt with **PySide6** and brought into the Snap ecosystem.

StaxWord proved the idea.

Otter gets to take it swimming.

Along the way, SnapWord gets a new home, a cleaner identity, an open-source future, and its own native document format:

### `.docs`

Because apparently nobody had claimed the obvious one.

---

## ✨ Features

* 🏠 **Local-first by default** — no account, no mandatory sync, no cloud dependency.
* ✍️ **Rich text editing** — fonts, colours, highlights, alignment, indentation, line spacing and more.
* 📋 **Lists & structured content** — ordered lists, unordered lists, block quotes and code blocks.
* 🖼️ **Insert the useful stuff** — images, links, tables and horizontal rules.
* 🗂️ **Multi-document tabs** — work across several documents without opening a small army of windows.
* 🔎 **Find & Replace** — because manually hunting through a document builds character, but we'd rather not.
* 🌗 **Light & dark themes** — with support for user-editable themes.
* 🖨️ **Print & PDF export** — get documents out of SnapWord without needing another application.
* 📄 **Native `.docs` documents** — SnapWord's own document format.

### Supported Formats

* **Open / Save:** `.docs`, `.docx`, `.odt`
* **Import:** `.rtf`, `.txt`, `.html`, `.md`
* **Export:** `.pdf`, `.rtf`, `.txt`, `.html`, `.md`

Use `.docs` for editable SnapWord documents with embedded images. DOCX and ODT
support basic formatted text, headings, lists, links, images and tables—not full
Word layout fidelity. Advanced numbering, merged/nested tables, comments, tracked
changes, headers and footers may not survive conversion. Keep the original;
SnapWord asks before importing or saving these formats.

RTF is text-only. Markdown retains supported markup, not page layout; TXT drops
formatting. Lossy exports require confirmation. Document and PDF writes replace
the destination only after the new file has been written successfully.

---

## 🚀 Installation

### Requirements

You'll need:

* **Python 3.10+**
* A desktop environment with a display server

For headless environments, Qt can also run using:

```bash
QT_QPA_PLATFORM=offscreen
```

### Run from source

Clone the repository and create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then install SnapWord:

```bash
python -m pip install -e .
```

---

## 🦦 Running SnapWord

Open a fresh document:

```bash
snapword
```

Jump straight into an existing document:

```bash
snapword file.docs
```

Check which Otter you've got:

```bash
snapword --version
```

That's it.

No server to start. No account to create. No browser tab pretending to be a desktop application.

---

## 💾 Where Does SnapWord Put Things?

Your **documents stay wherever you save them**.

SnapWord's own settings live in the platform's normal application configuration directory:

**Windows**

```text
%LOCALAPPDATA%\ZFordDev\SnapWord
```

**macOS**

```text
~/Library/Application Support/ZFordDev/SnapWord
```

**Linux**

```text
~/.config/ZFordDev/SnapWord
```

Application settings are stored in:

```text
settings.json
```

Need SnapWord to use somewhere else?

Set:

```text
SNAPWORD_CONFIG_DIR
```

and Otter will happily move house.

---

## 📦 Packaging

SnapWord's release build produces a standalone executable for each platform. The
Windows build also includes a per-user installer; Linux and macOS users run the
single-file executable directly. An automatic in-app updater is deferred.

Install the development dependencies:

```bash
python -m pip install -e ".[dev,build]"
```

Then build:

```bash
python scripts/build_icons.py
pyinstaller --noconfirm snapword.spec
python scripts/check_binary.py dist/snapword.exe
python scripts/package_release.py v0.1.0
```

Use `dist/snapword` for the binary check on Linux/macOS. The check verifies both
the version and bounded UI startup. The packaging command names a single-file
platform executable. On Windows, compile the installer with Inno Setup using:

```powershell
iscc /DAppVersion=0.1.0 /Odist-release installer/snapword.iss
```

The installer is per-user and offers Start Menu and optional desktop shortcuts.
GitHub Actions manual runs rehearse by default, while tag pushes publish
pre-releases with checksums. A manual publish can promote a verified tag to a
stable release. The draft SVG remains the icon source.

---

## 🛠️ Development & Tests

See [UI architecture and workspace customization](docs/UI_ARCHITECTURE.md) for
toolbar section ownership, layout persistence, theme styling, and regression checks.

Want to poke around inside the Otter?

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

Bug fixes, improvements, documentation changes and sensible amounts of chaos are welcome.

---

## 🌊 The Snap Ocean Suite

SnapWord isn't swimming alone.

It's part of the **Snap Ocean Suite** — a family of focused, local-first desktop tools built around a fairly simple idea:

> Your everyday software shouldn't need an account, subscription, or remote server just to do its job.

**SnapWord Otter** handles rich documents.

Other creatures are joining the water too. 🌊

---

## 📜 Licence

SnapWord is free and open-source software released under the [MIT License](LICENSE).

Use it. Fork it. Learn from it. Build something weird with it.

---

<div align="center">

Crafted with 🧠 & ☕ by **[ZFordDev](https://github.com/ZFordDev)**

**Local-first. No telemetry. No nonsense.**

🦦 **If Otter makes your writing life a little easier, throw SnapWord a star!** 🦦

</div>
