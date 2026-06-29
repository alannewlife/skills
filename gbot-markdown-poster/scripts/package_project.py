#!/usr/bin/env python3
"""
Package a Markdown directory for MarkdownPoster project ZIP import.

The generated ZIP contains an index.md plus an assets/ folder. Local image
references are copied into assets/ and rewritten to ./assets/<name>, so the
package can be imported by the deployed MarkdownPoster app without source code.
"""

import argparse
import hashlib
import mimetypes
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlparse


IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\n]+)\)")
SUPPORTED_IMAGE_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".svg",
    ".avif",
}


def split_markdown_target(raw: str) -> tuple[str, str]:
    target = raw.strip()
    if not target:
        return "", ""
    if target.startswith("<"):
        close = target.find(">")
        if close > 0:
            return target[1:close], target[close + 1 :]
    match = re.match(r"^(\S+)(\s+[\"'].*[\"'])?$", target)
    if match:
        return match.group(1), match.group(2) or ""
    return target, ""


def is_external_or_virtual(url: str) -> bool:
    if url.startswith("//"):
        return True
    parsed = urlparse(url)
    return bool(parsed.scheme) or url.startswith("local://")


def find_markdown(input_path: Path) -> Path:
    if input_path.is_file():
        return input_path
    index = input_path / "index.md"
    if index.exists():
        return index
    candidates = sorted(input_path.glob("*.md"))
    if candidates:
        return candidates[0]
    raise FileNotFoundError(f"No Markdown file found in {input_path}")


def asset_name_for(path: Path, used: set[str]) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", path.stem).strip("-") or "image"
    suffix = path.suffix.lower()
    digest = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:8]
    name = f"{stem}-{digest}{suffix}"
    counter = 2
    while name in used:
        name = f"{stem}-{digest}-{counter}{suffix}"
        counter += 1
    used.add(name)
    return name


def normalize_inline_images(markdown: str) -> str:
    return re.sub(r"：(!\[[^\]]+\]\([^)]+\))", "：\n\n\\1", markdown)


def build_package(source: Path, output: Path, normalize_inline: bool) -> tuple[int, int]:
    markdown_path = find_markdown(source)
    base_dir = markdown_path.parent
    markdown = markdown_path.read_text(encoding="utf-8")
    if normalize_inline:
        markdown = normalize_inline_images(markdown)

    copied: dict[Path, str] = {}
    used_names: set[str] = set()
    missing = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal missing
        alt = match.group(1)
        raw_target = match.group(2)
        actual_url, title_part = split_markdown_target(raw_target)
        if not actual_url or is_external_or_virtual(actual_url):
            return match.group(0)

        clean_url = actual_url.split("#", 1)[0].split("?", 1)[0]
        resolved = (base_dir / unquote(clean_url)).resolve()
        if not resolved.exists() or not resolved.is_file():
            missing += 1
            return match.group(0)

        if resolved.suffix.lower() not in SUPPORTED_IMAGE_EXTS:
            mime, _ = mimetypes.guess_type(str(resolved))
            if not (mime or "").startswith("image/"):
                return match.group(0)

        asset_name = copied.get(resolved)
        if not asset_name:
            asset_name = asset_name_for(resolved, used_names)
            copied[resolved] = asset_name

        return f"![{alt}](./assets/{asset_name}{title_part})"

    packaged_markdown = IMAGE_RE.sub(replace, markdown)

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("index.md", packaged_markdown)
        for src, asset_name in copied.items():
            zf.write(src, f"assets/{asset_name}")

    return len(copied), missing


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Package a Markdown directory as a MarkdownPoster import ZIP"
    )
    parser.add_argument("source", help="Markdown file or directory containing index.md")
    parser.add_argument(
        "-o",
        "--output",
        help="Output .zip path. Default: <source-name>.markdownposter.zip next to source",
    )
    parser.add_argument(
        "--keep-inline-images",
        action="store_true",
        help="Do not move inline image syntax onto its own paragraph",
    )
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        print(f"Error: source not found: {source}", file=sys.stderr)
        return 1

    default_name = f"{source.stem if source.is_file() else source.name}.markdownposter.zip"
    output = Path(args.output).expanduser().resolve() if args.output else source.parent / default_name

    try:
        image_count, missing_count = build_package(
            source,
            output,
            normalize_inline=not args.keep_inline_images,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Created: {output}")
    print(f"Packaged images: {image_count}")
    if missing_count:
        print(f"Missing local images: {missing_count}", file=sys.stderr)
    return 0 if missing_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
