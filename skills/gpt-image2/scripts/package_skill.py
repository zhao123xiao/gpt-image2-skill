#!/usr/bin/env python3
"""Package the gpt-image2 skill as a zip archive."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


DEFAULT_OUTPUT = Path.cwd() / "gpt-image2-skill.zip"
EXCLUDE_PARTS = {
    "__pycache__",
    "gpt-image2-output",
    "DreamfieldImage2Test",
    "processed-inputs",
    "generated-masks",
    "drawn-masks",
    "mask-overlays",
    "clipboard-inputs",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".tmp", ".response.json", ".summary.json"}
EXCLUDE_NAME_SUFFIXES = (".response.json", ".summary.json")


def should_include(path: Path, root: Path) -> bool:
    rel = path.relative_to(root.parent)
    if any(part in EXCLUDE_PARTS for part in rel.parts):
        return False
    if path.suffix in EXCLUDE_SUFFIXES or path.name.endswith(EXCLUDE_NAME_SUFFIXES):
        return False
    if path.name.startswith("."):
        return False
    return True


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    skill_dir = Path(__file__).resolve().parents[1]
    output_path = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else DEFAULT_OUTPUT
    output_path.parent.mkdir(parents=True, exist_ok=True)

    included: list[str] = []
    with ZipFile(output_path, "w", ZIP_DEFLATED) as archive:
        for path in sorted(skill_dir.rglob("*")):
            if not path.is_file() or not should_include(path, skill_dir):
                continue
            arcname = path.relative_to(skill_dir.parent).as_posix()
            archive.write(path, arcname)
            included.append(arcname)

    print(f"Package: {output_path}")
    print(f"Size: {output_path.stat().st_size} bytes")
    print(f"SHA256: {sha256(output_path)}")
    print("Files:")
    for name in included:
        print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
