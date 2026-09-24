"""Transactional replacement for document and export files."""
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def atomic_destination(path):
    destination = Path(path).resolve()
    descriptor, temporary = tempfile.mkstemp(prefix=f".{destination.stem}-", suffix=destination.suffix,
                                             dir=destination.parent)
    os.close(descriptor)
    temporary = Path(temporary)
    try:
        yield temporary
        with temporary.open("rb+") as stream:
            os.fsync(stream.fileno())
        if destination.exists():
            temporary.chmod(destination.stat().st_mode)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
