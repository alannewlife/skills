#!/usr/bin/env python3
"""Portable paths for style-reference assets bundled with this skill."""
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
IMAGE_ROOT = SKILL / "assets" / "images" / "individual"


def bucket_name(number: int | str) -> str:
    value = int(number)
    if value < 1:
        raise ValueError("Style number must be positive.")
    start = ((value - 1) // 200) * 200 + 1
    return f"{start:03}-{start + 199:03}"


def single_path(number: int | str) -> Path:
    value = int(number)
    return IMAGE_ROOT / bucket_name(value) / f"{value:03}.png"


def grid_path(number: int | str) -> Path:
    value = int(number)
    return IMAGE_ROOT / bucket_name(value) / f"{value:03}_grid.jpg"
