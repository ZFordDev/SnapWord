"""Ordered ODT import and Qt's rich ODF writer."""

import base64
import mimetypes
import zipfile
from html import escape
from xml.etree import ElementTree as ET

from PySide6.QtCore import QByteArray
from PySide6.QtGui import QTextDocument, QTextDocumentWriter
from PySide6.QtWidgets import QApplication

NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
    "fo": "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "draw": "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0",
    "xlink": "http://www.w3.org/1999/xlink",
}


def q(name):
    prefix, local = name.split(":")
    return f"{{{NS[prefix]}}}{local}"


def load_odt(path):
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("content.xml"))
        trees = [root]
        if "styles.xml" in archive.namelist():
            trees.append(ET.fromstring(archive.read("styles.xml")))
        styles = {node.get(q("style:name")): node for tree in trees for node in tree.iter(q("style:style"))}
        ordered = {
            node.get(q("style:name"))
            for tree in trees
            for node in tree.iter(q("text:list-style"))
            if node.find(q("text:list-level-style-number")) is not None
        }

        def css(name, seen=()):
            if name not in styles or name in seen:
                return ""
            node = styles[name]
            result = css(node.get(q("style:parent-style-name")), (*seen, name))
            for child in node:
                for key, value in child.attrib.items():
                    if key.startswith("{" + NS["fo"] + "}"):
                        prop = key.split("}")[1]
                        if prop in (
                            "font-size",
                            "font-weight",
                            "font-style",
                            "font-family",
                            "color",
                            "background-color",
                            "text-align",
                            "margin-left",
                            "margin-right",
                        ):
                            result += f"{prop}:{escape(value, quote=True)};"
                    elif key == q("style:text-underline-style") and value != "none":
                        result += "text-decoration:underline;"
            return result

        def render(node):
            tag = node.tag
            inline = tag in {q("text:p"), q("text:h"), q("text:span"), q("text:a")}
            content = (escape(node.text or "") if inline else "") + "".join(
                render(child) + (escape(child.tail or "") if inline else "") for child in node
            )
            style = css(node.get(q("text:style-name")))
            if tag == q("text:p"):
                return f'<p style="{style}">{content}</p>'
            if tag == q("text:h"):
                level = int(node.get(q("text:outline-level"), "1"))
                return f'<h{min(6, max(1, level))} style="{style}">{content}</h{min(6, max(1, level))}>'
            if tag == q("text:span"):
                return f'<span style="{style}">{content}</span>'
            if tag == q("text:a"):
                return f'<a href="{escape(node.get(q("xlink:href"), ""), quote=True)}">{content}</a>'
            if tag == q("text:list"):
                list_tag = "ol" if node.get(q("text:style-name")) in ordered else "ul"
                return f"<{list_tag}>{content}</{list_tag}>"
            if tag == q("text:list-item"):
                return f"<li>{content}</li>"
            if tag == q("text:line-break"):
                return "<br>"
            if tag == q("text:s"):
                return "&nbsp;" * int(node.get(q("text:c"), "1"))
            if tag == q("text:tab"):
                return "&#9;"
            if tag == q("table:table"):
                return f'<table border="1">{content}</table>'
            if tag == q("table:table-row"):
                return f"<tr>{content}</tr>"
            if tag == q("table:table-cell"):
                return f"<td>{content}</td>"
            if tag == q("draw:image"):
                source = node.get(q("xlink:href"), "").removeprefix("./")
                if source not in archive.namelist():
                    raise ValueError(f"ODT image is not embedded: {source}")
                kind = mimetypes.guess_type(source)[0] or "image/png"
                data = base64.b64encode(archive.read(source)).decode("ascii")
                return f'<img src="data:{kind};base64,{data}">'
            return content

        body = root.find("office:body/office:text", NS)
        if body is None:
            raise ValueError("No text body found in ODT document")
        return render(body)


def save_odt(path, html):
    app = QApplication.instance() or QApplication([])
    document = QTextDocument()
    document.setHtml(html)
    writer = QTextDocumentWriter(path, QByteArray(b"ODF"))
    if not writer.write(document):
        raise OSError("ODT export failed")
    del app
