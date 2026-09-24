"""Small release checks and checksum generation used by CI."""

import hashlib
import re
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def verify_tag(tag):
    match = re.fullmatch(r"v(?P<base>\d+\.\d+\.\d+)(?:[-+][0-9A-Za-z.-]+)?", tag)
    if not match:
        raise ValueError(f"Invalid release tag {tag!r}; expected vX.Y.Z or vX.Y.Z-prerelease")
    try:
        project_version = version("snapword")
    except PackageNotFoundError as exc:
        raise RuntimeError("Install the project before checking the release tag") from exc
    if match.group("base") != project_version:
        raise ValueError(f"Release tag {tag!r} does not match project version {project_version!r}")
    print(f"Verified {tag} against SnapWord {project_version}")


def write_checksums(directory):
    root = Path(directory)
    assets = sorted(path for path in root.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    if not assets:
        raise FileNotFoundError(f"No release assets found in {root}")
    lines = []
    for asset in assets:
        digest = hashlib.sha256()
        with asset.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        lines.append(f"{digest.hexdigest()}  {asset.name}")
    (root / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote SHA256SUMS for {len(assets)} assets")


def main(args):
    if len(args) == 2 and args[0] == "verify-tag":
        verify_tag(args[1])
    elif len(args) == 2 and args[0] == "checksums":
        write_checksums(args[1])
    else:
        raise SystemExit("Usage: release.py verify-tag <tag> | checksums <asset-directory>")


if __name__ == "__main__":
    main(sys.argv[1:])
