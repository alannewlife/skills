#!/usr/bin/env python3
"""Validate the self-contained installed skill and its generated resources."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from resolve_reference import resolve
from style_asset_paths import bucket_name, grid_path, single_path

SKILL = Path(__file__).resolve().parents[1]
REFERENCES = SKILL / "references"
IMAGES = SKILL / "assets" / "images"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> None:
    subprocess.run(
        [sys.executable, "-X", "utf8", str(SKILL / "scripts" / "build_library.py")],
        check=True,
    )
    styles = json.loads((REFERENCES / "styles.json").read_text(encoding="utf-8"))
    expected = [f"{number:03}" for number in range(1, len(styles) + 1)]
    if [item["number"] for item in styles] != expected:
        fail("style numbering is not continuous")
    if bucket_name(1) != "001-200" or bucket_name(217) != "201-400":
        fail("asset bucket calculation is incorrect")
    missing = [str(single_path(number)) for number in expected if not single_path(number).exists()]
    if missing:
        fail(f"missing numbered image assets; first missing: {missing[0]}")
    gallery = (SKILL / "gallery" / "index.html").read_text(encoding="utf-8")
    sheets = sorted(IMAGES.glob("[A-G]_*.png"))
    if not sheets or any(f"../assets/images/{path.name}" not in gallery for path in sheets):
        fail("gallery does not reference every bundled contact sheet")
    if "E:\\" in (SKILL / "SKILL.md").read_text(encoding="utf-8"):
        fail("SKILL.md contains a machine-specific Windows path")
    unknown = resolve("unregistered-model", "217")
    if not unknown["use_reference_image"] or unknown["reference_path"] != str(grid_path(217)):
        fail("reference-image fallback did not resolve the bundled grid asset")
    named = resolve("gpt-image-2", "001")
    if named["use_reference_image"]:
        fail("known name-activated style unexpectedly uses an image")
    print(f"PASS: self-contained skill with {len(styles)} styles, {len(sheets)} contact sheets, and portable asset paths.")


if __name__ == "__main__":
    main()
