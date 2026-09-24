"""Name standalone SnapWord release binaries for each supported platform."""

import platform
import shutil
import sys
from pathlib import Path


def normalized_architecture(machine):
    return {"amd64": "x86_64", "x64": "x86_64", "aarch64": "arm64"}.get(machine.lower(), machine.lower())


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: package_release.py <v-prefixed-tag> [dist-directory] [output-directory]")
    tag = sys.argv[1]
    distribution = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("dist")
    output = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("dist-release")
    system = {"darwin": "macos"}.get(platform.system().lower(), platform.system().lower())
    architecture = normalized_architecture(platform.machine())
    executable_name = "snapword.exe" if system == "windows" else "snapword"
    executable = distribution / executable_name
    if not executable.is_file():
        raise FileNotFoundError(executable)
    output.mkdir(parents=True, exist_ok=True)
    suffix = ".exe" if system == "windows" else ""
    asset = output / f"snapword-{tag}-{system}-{architecture}{suffix}"
    shutil.copy2(executable, asset)
    print(asset)


if __name__ == "__main__":
    main()
