<div align="center">

# SnapWord

### 🦦 Otter 🦦

**A friendly, local-first word processor that just wants to write.**

Your documents stay on your computer, right where you saved them.

</div>

---

## 💡 What is SnapWord?

SnapWord is a lightweight desktop word processor for everyday writing. Create
polished documents with formatted text, images, tables, lists, links, printing,
and PDF export without an account, a subscription, or a cloud dependency.

The otter is here to keep things simple: open the app, write something good,
and save it wherever you like. 🦦

## ✨ Features

- 🏠 **Local-first by default** — no account, mandatory sync, or telemetry.
- ✍️ **Rich text editing** — fonts, colours, highlights, alignment, indentation,
  line spacing, and more.
- 📋 **Structured writing** — ordered lists, unordered lists, block quotes, and
  code blocks.
- 🖼️ **Useful inserts** — images, links, tables, and horizontal rules.
- 🗂️ **Multi-document tabs** — keep several documents together without opening
  a small army of windows.
- 🔎 **Find and Replace** — find the right words quickly.
- 🌗 **Light and dark themes** — including user-editable themes.
- 🖨️ **Print and PDF export** — share your work when it is ready.
- 📄 **Native `.docs` documents** — SnapWord's own format, with embedded images.

## 🚀 Download and install

Download the latest release for [Windows, macOS, or Linux from GitHub
Releases](https://github.com/ZFordDev/SnapWord/releases).

Windows releases include a portable application and a per-user installer.
Linux and macOS releases provide a standalone executable.

## 🦦 Running SnapWord

Open a fresh document:

```bash
snapword

# Open an existing document:
snapword file.docs

# Check the installed version:
snapword --version
```

There is no server to start. Pick a document, give it a name, and let Otter do
the rest.

## 📄 Supported formats

- **Open and save:** `.docs`, `.docx`, `.odt`
- **Import:** `.rtf`, `.txt`, `.html`, `.md`
- **Export:** `.pdf`, `.rtf`, `.txt`, `.html`, `.md`

`.docs` is the best choice for editable SnapWord documents. DOCX and ODT support
common formatted text, headings, lists, links, images, and tables, but complex
Word layouts may change during conversion. SnapWord asks before an import or
save that may lose detail.

RTF is text-only. Markdown keeps supported markup rather than page layout, and
plain text does not keep formatting. Document and PDF saves replace the target
only after the new file has been written successfully.

## 🛠️ Run from source

SnapWord requires Python 3.10 or newer.

```bash
git clone https://github.com/ZFordDev/SnapWord.git
cd SnapWord
python -m venv .venv
```

Activate the environment, then install SnapWord:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

On macOS and Linux, activate the environment with:

```bash
source .venv/bin/activate
python -m pip install -e .
```

Contributor setup, tests, headless Qt checks, and release packaging are covered
in [Contributing to SnapWord](docs/CONTRIBUTING.md).

## 💾 Your files and settings

Your documents stay wherever you save them. SnapWord keeps its own preferences,
themes, and workspace layout in the platform's normal application settings
folder. Set `SNAPWORD_CONFIG_DIR` if you would like to choose a different
location.

## 🌊 The Snap Ocean Suite

SnapWord is part of the **Snap Ocean Suite**, a family of focused, local-first
desktop tools built around one simple idea:

> Everyday software should be ready when you are, without asking for an account
> just to do its job.

SnapWord Otter handles rich documents. More creatures are joining the water. 🌊

## 📜 Licence

SnapWord is free and open-source software released under the [MIT License](LICENSE).

Bug fixes, thoughtful improvements, documentation, and a little friendly chaos
are welcome.

<div align="center">

Crafted with 🧠 and ☕ by **[ZFordDev](https://github.com/ZFordDev)**

🦦 **If Otter makes writing a little easier, give SnapWord a star!** 🦦

</div>
