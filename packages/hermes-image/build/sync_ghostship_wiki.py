#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path


SOURCE = Path(os.environ.get("GHOSTSHIP_WIKI_SOURCE", "/opt/ghostship/ghostship-wiki"))
DEST = Path(os.environ.get("GHOSTSHIP_WIKI_DEST", str(Path.home() / "ghostship-wiki")))
MANIFEST_NAME = ".ghostship-managed-files"


def iter_source_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file())


def copy_managed_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        shutil.copyfile(source, tmp)
        shutil.copymode(source, tmp)
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink()


def main() -> None:
    if not SOURCE.exists():
        return

    DEST.mkdir(parents=True, exist_ok=True)
    managed: list[str] = []
    for source in iter_source_files(SOURCE):
        relative = source.relative_to(SOURCE)
        if relative.name == MANIFEST_NAME:
            continue
        target = DEST / relative
        copy_managed_file(source, target)
        managed.append(relative.as_posix())

    manifest = DEST / MANIFEST_NAME
    manifest.write_text(
        "# Repo-managed Ghostship wiki files. These may be overwritten by image updates.\n"
        "# Agent-created files outside this list are preserved.\n"
        + "\n".join(managed)
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
