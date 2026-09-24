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

SnapWord can be packaged as a standalone executable using **PyInstaller**.

Install the development dependencies:

```bash
python -m pip install -e ".[dev]" pyinstaller
```

Then build:

```bash
pyinstaller --onefile --name snapword --add-data "snapword/themes/*;snapword/themes" snapword_launcher.py
```

Tagged builds are published as GitHub Release assets.

---

## 🛠️ Development & Tests

Want to poke around inside the Otter?

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
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
