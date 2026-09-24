from __future__ import annotations

from html import escape
from pathlib import Path

from .docx_format import load_docx, save_docx
from .images import portable_html
from .odt_format import load_odt, save_odt
from .storage import atomic_destination

SUPPORTED_OPEN_FILTER = (
    "Documents (*.docs *.docx *.odt);;"
    "Import (*.rtf *.txt *.html *.htm *.md);;"
    "All Files (*)"
)
SUPPORTED_SAVE_FILTER = (
    "SnapWord Documents (*.docs);;"
    "Microsoft Word (*.docx);;"
    "OpenDocument Text (*.odt);;"
    "All Files (*)"
)


def _text_to_html(text: str) -> str:
    paragraphs = text.splitlines() or [""]
    return "".join(f"<p>{escape(paragraph)}</p>" for paragraph in paragraphs)


def load_as_html(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in {".docs", ".html", ".htm"}:
        return portable_html(Path(path).read_text(encoding="utf-8"), Path(path).parent)
    if suffix == ".txt":
        return _text_to_html(Path(path).read_text(encoding="utf-8"))
    if suffix == ".md":
        import markdown

        html = markdown.markdown(Path(path).read_text(encoding="utf-8"), extensions=["extra"])
        return portable_html(html, Path(path).parent)
    if suffix == ".rtf":
        from striprtf.striprtf import rtf_to_text

        text = rtf_to_text(Path(path).read_text(encoding="latin-1"))
        text = text.encode("utf-16", errors="surrogatepass").decode("utf-16", errors="replace")
        return _text_to_html(text)
    if suffix == ".docx":
        return load_docx(path)
    if suffix == ".odt":
        return load_odt(path)
    raise ValueError(f"Unsupported document format: {suffix or '(none)'}")


def save_document(path: str, html: str, plain_text: str) -> None:
    html = portable_html(html)
    with atomic_destination(path) as temporary:
        _write_document(str(temporary), html, plain_text)


def _write_document(path: str, html: str, plain_text: str) -> None:
    suffix = Path(path).suffix.lower()
    if suffix in {".docs", ".html", ".htm"}:
        Path(path).write_text(html, encoding="utf-8")
    elif suffix == ".txt":
        Path(path).write_text(plain_text, encoding="utf-8")
    elif suffix == ".md":
        from PySide6.QtGui import QTextDocument
        document = QTextDocument()
        document.setHtml(html)
        Path(path).write_text(document.toMarkdown(), encoding="utf-8")
    elif suffix == ".rtf":
        Path(path).write_text(_plain_text_to_rtf(plain_text), encoding="utf-8")
    elif suffix == ".docx":
        save_docx(path, html)
    elif suffix == ".odt":
        save_odt(path, html)
    else:
        raise ValueError(f"Unsupported document format: {suffix or '(none)'}")


def _plain_text_to_rtf(text: str) -> str:
    output = []
    for character in text:
        if character in "\\{}":
            output.append("\\" + character)
        elif character == "\n":
            output.append("\\par\n")
        elif character == "\t":
            output.append("\\tab ")
        elif ord(character) < 128:
            output.append(character)
        else:
            encoded = character.encode("utf-16-le")
            for offset in range(0, len(encoded), 2):
                unit = int.from_bytes(encoded[offset:offset + 2], "little", signed=True)
                output.append(f"\\u{unit}?")
    return r"{\rtf1\ansi\uc1\deff0 " + "".join(output) + "}"
