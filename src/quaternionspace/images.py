"""Download the images a conversion referenced."""

from __future__ import annotations

import os
import shutil
import urllib.request
from collections.abc import Iterable
from pathlib import Path

TIMEOUT = 30  # seconds per request


def download_images(items: Iterable[tuple[str, str]], dest: Path) -> tuple[int, int, list[str]]:
    """Fetch (url, filename) pairs into ``dest``. Existing files are skipped.

    Returns (downloaded, skipped, errors). Each transfer writes ``<name>.part`` and
    renames it on success, so an interrupted run never leaves a truncated file.
    """
    dest.mkdir(parents=True, exist_ok=True)
    ok = skipped = 0
    errors: list[str] = []
    for url, name in items:
        path = dest / name
        if path.exists():
            skipped += 1
            continue
        part = path.with_name(name + ".part")
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT) as resp, part.open("wb") as f:
                shutil.copyfileobj(resp, f)
            os.replace(part, path)
            ok += 1
        except OSError as e:  # URLError and HTTPError are OSError subclasses
            part.unlink(missing_ok=True)
            errors.append(f"{url}: {e}")
    return ok, skipped, errors
