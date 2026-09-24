"""Bounded checks for a built executable. Any failure propagates to CI."""
import os
import subprocess
import sys
from pathlib import Path


def main():
    binary = Path(sys.argv[1]).resolve()
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    for argument in ("--version", "--smoke-test"):
        subprocess.run([str(binary), argument], check=True, timeout=60, env=env)


if __name__ == "__main__":
    main()
