from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication


def _get_version() -> str:
    try:
        from importlib.metadata import version as _pkg_version

        return _pkg_version("snapword")
    except Exception:
        return "0.1.0"


def launch(file_path: str | None = None) -> int:
    """Launch SnapWord as an independent application."""
    from .branding import application_icon
    from .ui.window import SnapWordWindow

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setWindowIcon(application_icon())

    window = SnapWordWindow(version=_get_version())
    if file_path:
        window.load_file(file_path)
    window.show()

    return app.exec()


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] in ("--version", "-v", "-V"):
        print(f"SnapWord {_get_version()}")
        return 0

    if args == ["--smoke-test"]:
        import os
        import tempfile

        from PySide6.QtCore import QTimer

        with tempfile.TemporaryDirectory(prefix="snapword-smoke-") as config:
            os.environ["SNAPWORD_CONFIG_DIR"] = config
            app = QApplication.instance() or QApplication([sys.argv[0]])
            from .ui.window import SnapWordWindow
            window = SnapWordWindow(version=_get_version())
            window.show()
            if window.windowIcon().isNull() or len(window.toolbar_sections) != 13:
                return 1
            QTimer.singleShot(100, app.quit)
            result = app.exec()
            window.hide()
            print("SnapWord startup smoke test passed")
            return result

    return launch(args[0] if args else None)


if __name__ == "__main__":
    sys.exit(main())
