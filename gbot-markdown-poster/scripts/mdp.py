#!/usr/bin/env python3
"""
MarkdownPoster local CLI.

The `open` command reads a local Markdown file or directory, builds a Markdown
plus image-pool payload, and opens MarkdownPoster through a temporary loopback
bridge endpoint.
"""

import argparse
import base64
import json
import mimetypes
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


BRIDGE_PROTOCOL = "markdownposter.bridge"
DEFAULT_IMPORT_URL = "https://rrzxs.com/mdp/import"
DEFAULT_TIMEOUT_SECONDS = 30
MAX_MARKDOWN_BYTES = 200 * 1024
MAX_IMAGE_POOL_BYTES = int(4.8 * 1024 * 1024)
DEFAULT_CHANNEL = "bridge"
HASH_MARKDOWN_BYTES = 64 * 1024
SUPPORTED_IMAGE_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".svg",
    ".avif",
}

MARKDOWN_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\n]+)\)")
HTML_IMG_SRC_RE = re.compile(r"(<img\b[^>]*?\bsrc=[\"'])([^\"']+)([\"'][^>]*>)", re.IGNORECASE)


class CliWarningCollector:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def add(self, message: str) -> None:
        self.messages.append(message)


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


def normalize_import_url(raw_url: str) -> str:
    parsed = urllib.parse.urlparse(raw_url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("--base-url must be an absolute http(s) URL")

    path = parsed.path or "/"
    if not path.endswith("/import"):
        path = path.rstrip("/") + "/import"

    return urllib.parse.urlunparse(parsed._replace(path=path, params="", query="", fragment=""))


def normalize_app_url(raw_url: str) -> str:
    parsed = urllib.parse.urlparse(raw_url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("--base-url must be an absolute http(s) URL")

    path = parsed.path or "/"
    if path.endswith("/import"):
        path = path[: -len("/import")] or "/"

    if not path.endswith("/"):
        path = f"{path}/"

    return urllib.parse.urlunparse(parsed._replace(path=path, params="", query="", fragment=""))


def encode_markdown_hash(markdown: str) -> str:
    encoded = base64.b64encode(markdown.encode("utf-8")).decode("ascii")
    return encoded.replace("+", "-").replace("/", "_")


def build_hash_url(base_url: str, markdown: str, source: str | None = None) -> str:
    app_url = normalize_app_url(base_url)
    parsed = urllib.parse.urlparse(app_url)
    query = urllib.parse.parse_qs(parsed.query)
    if source:
        query["mp_source"] = [source]
    encoded = urllib.parse.urlencode(query, doseq=True)
    hash_payload = urllib.parse.urlencode({"mpmd": encode_markdown_hash(markdown)})
    return urllib.parse.urlunparse(parsed._replace(query=encoded, fragment=hash_payload))


def read_sips_width(path: Path) -> int | None:
    if not shutil.which("sips"):
        return None
    try:
        result = subprocess.run(
            ["sips", "-g", "pixelWidth", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None

    match = re.search(r"pixelWidth:\s*(\d+)", result.stdout)
    return int(match.group(1)) if match else None


def maybe_prepare_image(
    path: Path,
    max_image_width: int | None,
    jpeg_quality: int | None,
    temp_dir: Path,
    warnings: CliWarningCollector,
) -> Path:
    if not max_image_width and jpeg_quality is None:
        return path

    suffix = path.suffix.lower()
    is_jpeg = suffix in {".jpg", ".jpeg"}
    can_resize = suffix in {".png", ".jpg", ".jpeg"}
    can_quality = is_jpeg
    if not can_resize and not can_quality:
        warnings.add(f"compression skipped for unsupported format: {path.name}")
        return path

    if not shutil.which("sips"):
        warnings.add("compression requested but macOS sips is not available; using original images")
        return path

    should_resize = False
    if max_image_width and can_resize:
        width = read_sips_width(path)
        should_resize = width is not None and width > max_image_width

    should_quality = jpeg_quality is not None and can_quality
    if not should_resize and not should_quality:
        return path

    out_path = temp_dir / f"{secrets.token_hex(8)}{suffix}"
    command = ["sips"]
    if should_resize and max_image_width:
        command.extend(["--resampleWidth", str(max_image_width)])
    if should_quality and jpeg_quality is not None:
        command.extend(["--setProperty", "formatOptions", str(jpeg_quality)])
    command.extend([str(path), "--out", str(out_path)])

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except Exception as exc:
        warnings.add(f"compression failed for {path.name}: {exc}")
        return path

    if out_path.exists() and out_path.stat().st_size < path.stat().st_size:
        return out_path

    warnings.add(f"compression did not reduce {path.name}; using original")
    return path


def data_url_for_image(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    if not mime:
        if path.suffix.lower() == ".svg":
            mime = "image/svg+xml"
        else:
            mime = "application/octet-stream"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def resolve_local_image(base_dir: Path, raw_url: str) -> Path | None:
    clean_url = raw_url.split("#", 1)[0].split("?", 1)[0]
    if not clean_url:
        return None

    decoded = unquote(clean_url)
    candidate = Path(decoded)
    if not candidate.is_absolute():
        candidate = base_dir / decoded

    resolved = candidate.resolve()
    if not resolved.exists() or not resolved.is_file():
        return None

    if resolved.suffix.lower() in SUPPORTED_IMAGE_EXTS:
        return resolved

    mime, _ = mimetypes.guess_type(str(resolved))
    if (mime or "").startswith("image/"):
        return resolved

    return None


def build_bridge_payload(
    source: Path,
    max_image_width: int | None = None,
    jpeg_quality: int | None = None,
) -> tuple[dict[str, object], int, int, list[str]]:
    markdown_path = find_markdown(source)
    base_dir = markdown_path.parent
    markdown = markdown_path.read_text(encoding="utf-8")

    image_pool: dict[str, str] = {}
    path_to_id: dict[Path, str] = {}
    warnings = CliWarningCollector()
    temp_dir_obj = tempfile.TemporaryDirectory(prefix="markdownposter-cli-")
    temp_dir = Path(temp_dir_obj.name)
    missing = 0

    def image_id_for(path: Path) -> str:
        existing = path_to_id.get(path)
        if existing:
            return existing

        image_id = f"img_{secrets.token_hex(5)}"
        while image_id in image_pool:
            image_id = f"img_{secrets.token_hex(5)}"

        prepared = maybe_prepare_image(path, max_image_width, jpeg_quality, temp_dir, warnings)
        image_pool[image_id] = data_url_for_image(prepared)
        path_to_id[path] = image_id
        return image_id

    def local_url_for_target(raw_target: str) -> str | None:
        nonlocal missing
        actual_url, _title_part = split_markdown_target(raw_target)
        if not actual_url or is_external_or_virtual(actual_url):
            return None

        resolved = resolve_local_image(base_dir, actual_url)
        if not resolved:
            missing += 1
            return None

        return f"local://{image_id_for(resolved)}"

    def replace_markdown_image(match: re.Match[str]) -> str:
        raw_target = match.group(2)
        _actual_url, title_part = split_markdown_target(raw_target)
        local_url = local_url_for_target(raw_target)
        if not local_url:
            return match.group(0)
        return f"![{match.group(1)}]({local_url}{title_part})"

    def replace_html_image(match: re.Match[str]) -> str:
        actual_url = match.group(2).strip()
        if not actual_url or is_external_or_virtual(actual_url):
            return match.group(0)

        local_url = local_url_for_target(actual_url)
        if not local_url:
            return match.group(0)

        return f"{match.group(1)}{local_url}{match.group(3)}"

    markdown = MARKDOWN_IMAGE_RE.sub(replace_markdown_image, markdown)
    markdown = HTML_IMG_SRC_RE.sub(replace_html_image, markdown)

    if len(markdown.encode("utf-8")) > MAX_MARKDOWN_BYTES:
        raise ValueError("Markdown payload exceeds 200KB bridge limit")

    image_pool_size = len(json.dumps(image_pool, ensure_ascii=False))
    if image_pool_size > MAX_IMAGE_POOL_BYTES:
        raise ValueError("Image payload exceeds MarkdownPoster local image pool limit")

    payload = {
        "protocol": BRIDGE_PROTOCOL,
        "version": 1,
        "source": f"markdownposter-cli:{markdown_path.name}",
        "markdown": markdown,
        "imagePool": image_pool,
    }
    temp_dir_obj.cleanup()
    return payload, len(image_pool), missing, warnings.messages


class BridgeServer:
    def __init__(self, payload: dict[str, object], token: str, allowed_origin: str, verbose: bool = False):
        self.payload = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.token = token
        self.allowed_origin = allowed_origin
        self.verbose = verbose
        self.served = threading.Event()
        self.completed = threading.Event()
        self.completion_status = ""
        self.completion_message = ""
        self.httpd: ThreadingHTTPServer | None = None

    def start(self) -> tuple[str, int]:
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:
                if bridge.verbose:
                    print(f"{self.command} {self.path} - {format % args}", flush=True)

            def send_cors_headers(self) -> None:
                self.send_header("Access-Control-Allow-Origin", bridge.allowed_origin)
                self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")
                self.send_header("Access-Control-Allow-Private-Network", "true")

            def do_OPTIONS(self) -> None:
                self.send_response(204)
                self.send_cors_headers()
                self.end_headers()

            def do_GET(self) -> None:
                parsed = urllib.parse.urlparse(self.path)
                query = urllib.parse.parse_qs(parsed.query)
                if query.get("token", [""])[0] != bridge.token:
                    self.send_response(404)
                    self.send_cors_headers()
                    self.end_headers()
                    return

                if parsed.path == "/done":
                    bridge.completion_status = query.get("status", ["ok"])[0]
                    bridge.completion_message = query.get("message", [""])[0]
                    bridge.completed.set()
                    self.send_response(204)
                    self.send_cors_headers()
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    return

                if parsed.path != "/payload":
                    self.send_response(404)
                    self.send_cors_headers()
                    self.end_headers()
                    return

                self.send_response(200)
                self.send_cors_headers()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(bridge.payload)))
                self.end_headers()
                try:
                    self.wfile.write(bridge.payload)
                    bridge.served.set()
                except BrokenPipeError:
                    return

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        thread.start()
        host, port = self.httpd.server_address
        return host, int(port)

    def shutdown(self) -> None:
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()


class SenderServer:
    def __init__(
        self,
        payload: dict[str, object],
        token: str,
        import_url: str,
        timeout_seconds: int,
        verbose: bool = False,
    ):
        self.payload_json = json.dumps(payload, ensure_ascii=False)
        self.token = token
        self.import_url = import_url
        self.timeout_seconds = timeout_seconds
        self.verbose = verbose
        self.completed = threading.Event()
        self.completion_status = ""
        self.completion_message = ""
        self.httpd: ThreadingHTTPServer | None = None
        self.sender_origin = "http://localhost"

    def start(self) -> tuple[str, int]:
        sender = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:
                if sender.verbose:
                    print(f"{self.command} {self.path} - {format % args}", flush=True)

            def send_no_store(self) -> None:
                self.send_header("Cache-Control", "no-store")

            def do_GET(self) -> None:
                parsed = urllib.parse.urlparse(self.path)
                query = urllib.parse.parse_qs(parsed.query)
                if parsed.path == "/sender" and query.get("token", [""])[0] == sender.token:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_no_store()
                    body = sender.build_sender_html().encode("utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return

                if parsed.path == "/done" and query.get("token", [""])[0] == sender.token:
                    sender.completion_status = query.get("status", ["ok"])[0]
                    sender.completion_message = query.get("message", [""])[0]
                    sender.completed.set()
                    self.send_response(204)
                    self.send_no_store()
                    self.end_headers()
                    return

                self.send_response(404)
                self.send_no_store()
                self.end_headers()

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        host, port = self.httpd.server_address
        self.sender_origin = f"http://localhost:{int(port)}"
        thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        thread.start()
        return host, int(port)

    def build_sender_html(self) -> str:
        nonce = secrets.token_urlsafe(18)
        import_url = urllib.parse.urlparse(self.import_url)
        query = urllib.parse.parse_qs(import_url.query)
        query["mp_channel"] = ["pm"]
        query["mp_nonce"] = [nonce]
        query["mp_source"] = [self.sender_origin]
        target_url = urllib.parse.urlunparse(import_url._replace(query=urllib.parse.urlencode(query, doseq=True)))
        target_origin = f"{import_url.scheme}://{import_url.netloc}"
        escaped_payload = self.payload_json.replace("</", "<\\/")
        timeout_ms = max(1, int(self.timeout_seconds)) * 1000

        return f"""<!doctype html>
<meta charset="utf-8">
<title>Opening MarkdownPoster...</title>
<style>
  html, body {{ height: 100%; margin: 0; }}
  body {{ font: 13px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #1f2937; background: #fff; }}
  iframe {{ width: 100%; height: 100%; border: 0; display: block; }}
  #status {{
    position: fixed;
    left: 12px;
    bottom: 12px;
    z-index: 2147483647;
    max-width: min(520px, calc(100vw - 24px));
    padding: 6px 9px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.92);
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.12);
  }}
  #status.done {{ opacity: 0; pointer-events: none; transition: opacity 240ms ease; }}
  #status.error {{ color: #b91c1c; }}
</style>
<iframe id="target" src="{target_url}"></iframe>
<div id="status">Opening MarkdownPoster...</div>
<script id="payload" type="application/json">{escaped_payload}</script>
<script>
(function () {{
  var payload = JSON.parse(document.getElementById('payload').textContent);
  var targetOrigin = {json.dumps(target_origin)};
  var nonce = {json.dumps(nonce)};
  var doneUrl = '/done?token={urllib.parse.quote(self.token)}';
  var status = document.getElementById('status');
  var frame = document.getElementById('target');
  var child = frame.contentWindow;

  function finish(state, code, message) {{
    var url = doneUrl + '&status=' + encodeURIComponent(state);
    if (code) url += '&code=' + encodeURIComponent(code);
    if (message) url += '&message=' + encodeURIComponent(message);
    fetch(url).catch(function () {{}});
    status.textContent = state === 'ok' ? 'MarkdownPoster import delivered.' : ('Import failed: ' + (message || code || state));
    status.className = state === 'ok' ? 'done' : 'error';
  }}

  var timeoutId = window.setTimeout(function () {{
    finish('timeout', 'timeout', 'MarkdownPoster did not acknowledge the import');
  }}, {timeout_ms});

  window.addEventListener('message', function (event) {{
    if (event.source !== child || event.origin !== targetOrigin) return;
    var data = event.data || {{}};

    if (data.type === 'markdownposter.import.ready') {{
      if (data.nonce && data.nonce !== nonce) return;
      child.postMessage({{
        type: 'markdownposter.import.payload',
        nonce: nonce,
        markdown: payload.markdown,
        imagePool: payload.imagePool,
        source: payload.source || 'markdownposter-cli',
        version: 1
      }}, targetOrigin);
      status.textContent = 'Payload sent to MarkdownPoster...';
      return;
    }}

    if (data.type === 'markdownposter.import.ack') {{
      if (data.nonce && data.nonce !== nonce) return;
      window.clearTimeout(timeoutId);
      finish(data.status === 'ok' ? 'ok' : 'error', data.code || '', data.message || '');
    }}
  }});
}})();
</script>
"""

    def shutdown(self) -> None:
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()


def build_import_url(import_url: str, endpoint: str, ack_endpoint: str, token: str) -> str:
    parsed = urllib.parse.urlparse(import_url)
    query = urllib.parse.parse_qs(parsed.query)
    query["mp_channel"] = ["bridge"]
    query["mp_endpoint"] = [endpoint]
    query["mp_ack"] = [ack_endpoint]
    query["mp_token"] = [token]
    return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(query, doseq=True)))


def build_sender_url(port: int, token: str) -> str:
    return f"http://localhost:{port}/sender?token={urllib.parse.quote(token)}"


def open_url_in_browser(url: str) -> None:
    opener = shutil.which("open")
    if opener:
        subprocess.run([opener, url], check=False)
        return
    webbrowser.open(url)


def run_bridge_channel(args: argparse.Namespace, import_url: str, payload: dict[str, object]) -> int:
    token = secrets.token_urlsafe(24)
    allowed_origin = f"{urllib.parse.urlparse(import_url).scheme}://{urllib.parse.urlparse(import_url).netloc}"
    server = BridgeServer(payload, token, allowed_origin, verbose=args.verbose)
    _host, port = server.start()
    endpoint = f"http://127.0.0.1:{port}/payload"
    ack_endpoint = f"http://127.0.0.1:{port}/done"
    open_url = build_import_url(import_url, endpoint, ack_endpoint, token)

    print(f"MarkdownPoster bridge URL: {open_url}", flush=True)
    if not args.no_open:
        open_url_in_browser(open_url)

    try:
        if not server.completed.wait(args.timeout_seconds):
            if server.served.is_set():
                print("Error: bridge payload was fetched, but MarkdownPoster did not acknowledge import completion", file=sys.stderr, flush=True)
            else:
                print("Error: bridge payload was not requested before timeout", file=sys.stderr, flush=True)
            print(f"Retry manually: {open_url}", file=sys.stderr, flush=True)
            print("Hint: use --verbose to inspect local bridge requests, or retry with --channel sender as a fallback.", file=sys.stderr, flush=True)
            return 2
        if server.completion_status != "ok":
            details = f": {server.completion_message}" if server.completion_message else ""
            print(f"Error: bridge reported status {server.completion_status}{details}", file=sys.stderr, flush=True)
            return 2
        time.sleep(2.0)
        print("Bridge import completed in MarkdownPoster.", flush=True)
        return 0
    finally:
        server.shutdown()


def run_sender_channel(args: argparse.Namespace, import_url: str, payload: dict[str, object]) -> int:
    token = secrets.token_urlsafe(24)
    server = SenderServer(payload, token, import_url, args.timeout_seconds, verbose=args.verbose)
    _host, port = server.start()
    sender_url = build_sender_url(port, token)

    print(f"MarkdownPoster sender URL: {sender_url}", flush=True)
    print(f"Target import URL: {import_url}", flush=True)
    if not args.no_open:
        open_url_in_browser(sender_url)

    try:
        if not server.completed.wait(args.timeout_seconds):
            print("Error: sender did not complete before timeout", file=sys.stderr, flush=True)
            print(f"Retry manually: {sender_url}", file=sys.stderr, flush=True)
            print("Hint: keep the local sender page open; it embeds MarkdownPoster and sends the payload with postMessage.", file=sys.stderr, flush=True)
            return 2
        if server.completion_status != "ok":
            details = f": {server.completion_message}" if server.completion_message else ""
            print(f"Error: sender reported status {server.completion_status}{details}", file=sys.stderr, flush=True)
            return 2
        print("Sender import payload delivered.", flush=True)
        return 0
    finally:
        server.shutdown()


def run_hash_channel(args: argparse.Namespace, base_url: str, payload: dict[str, object]) -> int:
    markdown = str(payload.get("markdown") or "")
    markdown_bytes = len(markdown.encode("utf-8"))
    if payload.get("imagePool"):
        print("Error: hash channel cannot carry local images; use the default bridge channel instead.", file=sys.stderr)
        return 2
    if markdown_bytes > HASH_MARKDOWN_BYTES:
        print("Error: markdown is too large for hash channel; use the default bridge channel instead.", file=sys.stderr)
        return 2

    open_url = build_hash_url(base_url, markdown, source=str(payload.get("source") or "markdownposter-cli"))
    print(f"MarkdownPoster hash URL: {open_url}", flush=True)
    if not args.no_open:
        open_url_in_browser(open_url)
    return 0


def command_open(args: argparse.Namespace) -> int:
    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        print(f"Error: source not found: {source}", file=sys.stderr)
        return 1

    try:
        import_url = normalize_import_url(args.base_url)
        payload, image_count, missing_count, warnings = build_bridge_payload(
            source,
            max_image_width=args.max_image_width,
            jpeg_quality=args.jpeg_quality,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Prepared images: {image_count}", flush=True)
    if missing_count:
        print(f"Warning: missing local images: {missing_count}", file=sys.stderr, flush=True)
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr, flush=True)

    if args.channel == "hash":
        return run_hash_channel(args, args.base_url, payload)
    if args.channel == "sender":
        return run_sender_channel(args, import_url, payload)
    return run_bridge_channel(args, import_url, payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="MarkdownPoster local CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    open_parser = subparsers.add_parser("open", help="Open a Markdown file or directory in MarkdownPoster")
    open_parser.add_argument("source", help="Markdown file or directory containing index.md")
    open_parser.add_argument(
        "--base-url",
        default=DEFAULT_IMPORT_URL,
        help=f"MarkdownPoster import URL (default: {DEFAULT_IMPORT_URL})",
    )
    open_parser.add_argument(
        "--channel",
        choices=["bridge", "sender", "hash"],
        default=DEFAULT_CHANNEL,
        help="Import channel. bridge opens the real MarkdownPoster page and is the default; sender uses a postMessage iframe fallback; hash is for short Markdown without local images.",
    )
    open_parser.add_argument("--no-open", action="store_true", help="Print the import URL without opening a browser")
    open_parser.add_argument("--verbose", action="store_true", help="Print local sender/bridge HTTP requests")
    open_parser.add_argument(
        "--max-image-width",
        type=int,
        default=None,
        help="Optionally downscale PNG/JPEG images wider than this many pixels using macOS sips",
    )
    open_parser.add_argument(
        "--jpeg-quality",
        type=int,
        default=None,
        help="Optionally recompress JPEG images using macOS sips formatOptions quality (1-100)",
    )
    open_parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Import delivery timeout (default: {DEFAULT_TIMEOUT_SECONDS})",
    )
    open_parser.set_defaults(func=command_open)

    args = parser.parse_args()
    if getattr(args, "jpeg_quality", None) is not None and not (1 <= args.jpeg_quality <= 100):
        parser.error("--jpeg-quality must be between 1 and 100")
    if getattr(args, "max_image_width", None) is not None and args.max_image_width <= 0:
        parser.error("--max-image-width must be greater than 0")
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
