#!/usr/bin/env python3
"""Generate WeChat article images with Agnes Image 2.1 Flash."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = SKILL_DIR / "config" / "agnes.env"
DEFAULT_BASE_URL = "https://apihub.agnes-ai.com"
DEFAULT_MODEL = "agnes-image-2.1-flash"
PLACEHOLDER_KEYS = {
    "",
    "YOUR_AGNES_API_KEY_HERE",
    "YOUR_API_KEY_HERE",
    "PASTE_YOUR_KEY_HERE",
}


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def sanitize_filename(value: str, default: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    if not name:
        name = default
    if not Path(name).suffix:
        name += ".png"
    return name


def read_json_jobs(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    direct_jobs = parse_json_value(text)
    if direct_jobs is not None:
        return direct_jobs

    jobs: list[dict[str, Any]] = []
    for match in re.finditer(r"```json\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE):
        parsed = parse_json_value(match.group(1))
        if parsed:
            jobs.extend(parsed)
    if not jobs:
        raise SystemExit(f"No JSON prompt blocks found in {path}")
    return jobs


def parse_json_value(text: str) -> list[dict[str, Any]] | None:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(value, dict):
        if "prompt" in value:
            return [value]
        if "images" in value and isinstance(value["images"], list):
            return [item for item in value["images"] if isinstance(item, dict)]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return None


def request_image(
    *,
    api_key: str,
    base_url: str,
    model: str,
    prompt: str,
    size: str,
    response_format: str,
    timeout: int,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "size": size,
    }
    if response_format == "base64":
        payload["return_base64"] = True
    else:
        payload["extra_body"] = {"response_format": "url"}

    req = urllib.request.Request(
        f"{normalize_base_url(base_url)}/v1/images/generations",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Agnes API error {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Agnes API request failed: {exc}") from exc


def save_result(data: dict[str, Any], output_path: Path, timeout: int) -> None:
    items = data.get("data")
    if not isinstance(items, list) or not items:
        raise SystemExit(f"Unexpected Agnes API response: {json.dumps(data, ensure_ascii=False)}")
    item = items[0]
    if not isinstance(item, dict):
        raise SystemExit(f"Unexpected Agnes API item: {item!r}")

    b64_data = item.get("b64_json")
    if isinstance(b64_data, str) and b64_data:
        if "," in b64_data and b64_data.startswith("data:"):
            b64_data = b64_data.split(",", 1)[1]
        output_path.write_bytes(base64.b64decode(b64_data))
        return

    image_url = item.get("url")
    if isinstance(image_url, str) and image_url:
        with urllib.request.urlopen(image_url, timeout=timeout) as response:
            output_path.write_bytes(response.read())
        return

    raise SystemExit(f"Agnes response did not include b64_json or url: {json.dumps(data, ensure_ascii=False)}")


def parse_size(size: str) -> tuple[int, int] | None:
    match = re.fullmatch(r"\s*(\d+)\s*x\s*(\d+)\s*", size)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def read_image_size(path: Path) -> tuple[int, int] | None:
    sips = shutil.which("sips")
    if not sips:
        return None
    proc = subprocess.run(
        [sips, "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    width_match = re.search(r"pixelWidth:\s*(\d+)", proc.stdout)
    height_match = re.search(r"pixelHeight:\s*(\d+)", proc.stdout)
    if not width_match or not height_match:
        return None
    return int(width_match.group(1)), int(height_match.group(1))


def enforce_size(path: Path, size: str, resize_mode: str) -> None:
    if resize_mode == "none":
        return
    target = parse_size(size)
    if not target:
        print(f"warning: cannot parse size {size!r}; leaving original dimensions", file=sys.stderr)
        return

    current = read_image_size(path)
    if current == target:
        return
    if current is None:
        print("warning: cannot read image dimensions; leaving original dimensions", file=sys.stderr)
        return

    sips = shutil.which("sips")
    if not sips:
        print("warning: sips not available; leaving original dimensions", file=sys.stderr)
        return

    current_w, current_h = current
    target_w, target_h = target
    current_ratio = current_w / current_h
    target_ratio = target_w / target_h

    if current_ratio > target_ratio:
        crop_h = current_h
        crop_w = round(current_h * target_ratio)
    else:
        crop_w = current_w
        crop_h = round(current_w / target_ratio)

    with tempfile.TemporaryDirectory(prefix="agnes-image-") as tmp_dir:
        cropped = Path(tmp_dir) / "cropped.png"
        subprocess.run(
            [sips, "--cropToHeightWidth", str(crop_h), str(crop_w), str(path), "--out", str(cropped)],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [sips, "--resampleHeightWidth", str(target_h), str(target_w), str(cropped), "--out", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )


def build_jobs(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.batch_json:
        return read_json_jobs(Path(args.batch_json))
    if args.prompt_file:
        return [
            {
                "filename": args.filename or Path(args.prompt_file).with_suffix(".png").name,
                "prompt": Path(args.prompt_file).read_text(encoding="utf-8").strip(),
                "size": args.size,
            }
        ]
    if args.prompt:
        return [{"filename": args.filename, "prompt": args.prompt, "size": args.size}]
    raise SystemExit("Provide --prompt, --prompt-file, or --batch-json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate images with Agnes Image 2.1 Flash.")
    parser.add_argument("--prompt", help="Single image prompt.")
    parser.add_argument("--prompt-file", help="Text file containing one prompt.")
    parser.add_argument("--batch-json", help="JSON file, or Markdown file with fenced JSON prompt blocks.")
    parser.add_argument("--filename", default="image.png", help="Output filename for single prompt mode.")
    parser.add_argument("--output-dir", default="outputs/images", help="Directory to save generated images.")
    parser.add_argument("--size", default="900x600", help="Image size, for example 900x600.")
    parser.add_argument("--model", help=f"Image model. Defaults to {DEFAULT_MODEL}.")
    parser.add_argument("--base-url", help=f"Agnes API base URL. Defaults to {DEFAULT_BASE_URL}.")
    parser.add_argument("--env-file", default=os.environ.get("AGNES_ENV_FILE", str(DEFAULT_ENV_FILE)))
    parser.add_argument("--response-format", choices=["base64", "url"], default="base64")
    parser.add_argument(
        "--resize-mode",
        choices=["cover", "none"],
        default="cover",
        help="Post-process to exact --size with center crop and resize, or keep original dimensions.",
    )
    parser.add_argument("--timeout", type=int, default=180)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_env_file(Path(args.env_file))
    args.model = args.model or os.environ.get("AGNES_IMAGE_MODEL", DEFAULT_MODEL)
    args.base_url = args.base_url or os.environ.get("AGNES_BASE_URL", DEFAULT_BASE_URL)

    api_key = os.environ.get("AGNES_API_KEY", "").strip()
    if api_key in PLACEHOLDER_KEYS:
        raise SystemExit(
            "AGNES_API_KEY is not set. Edit "
            f"{DEFAULT_ENV_FILE} or export AGNES_API_KEY before generating images."
        )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    for index, job in enumerate(build_jobs(args), start=1):
        prompt = str(job.get("prompt", "")).strip()
        if not prompt:
            raise SystemExit(f"Job {index} is missing prompt")
        size = str(job.get("size") or args.size)
        filename_seed = str(job.get("filename") or job.get("name") or f"{index:02d}.png")
        filename = sanitize_filename(filename_seed, f"{index:02d}.png")
        output_path = output_dir / filename

        data = request_image(
            api_key=api_key,
            base_url=args.base_url,
            model=args.model,
            prompt=prompt,
            size=size,
            response_format=args.response_format,
            timeout=args.timeout,
        )
        save_result(data, output_path, args.timeout)
        enforce_size(output_path, size, args.resize_mode)
        saved.append(str(output_path))
        print(f"saved {output_path}")

    print(json.dumps({"images": saved}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
