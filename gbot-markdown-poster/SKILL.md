---
name: gbot-markdown-poster
description: Open local Markdown files in MarkdownPoster web application for viewing and sharing. Use when you need to display Markdown documents in a beautiful web interface, share Markdown content via URL, or convert local Markdown files to viewable web pages. Triggers when users mention "open markdown in browser", "show markdown online", "markdown to web", "MarkdownPoster", or want to display Markdown content in a styled web viewer.
---

# Markdown Poster

## Overview

This skill enables opening local Markdown files in the MarkdownPoster web application (https://rrzxs.com/mdp/), which provides a beautiful, styled interface for viewing and sharing Markdown content.

## Quick Start

### Basic Usage

To open a Markdown file in MarkdownPoster:

```bash
python3 scripts/mdp.py open <path-to-markdown-file>
```

### Markdown Directory With Images

To open a directory containing `index.md` and local images without manually
importing a ZIP, use the local CLI:

```bash
python3 scripts/mdp.py open <path-to-markdown-directory>
```

The CLI:
- Finds `index.md` or the first `.md` file
- Reads referenced local images from the same directory tree
- Rewrites local image references such as `./assets/a.png` to
  `local://img_xxx`
- Stores local image data in the browser's local image pool
- Sends Markdown plus image data through a temporary loopback bridge
- Opens the real MarkdownPoster `/import` page as the top-level browser page;
  the page pulls the payload and acknowledges completion
- Leaves external, `data:`, and `local://` images unchanged

Use `--base-url http://localhost:3000/import` when testing a local dev server.

If an environment blocks loopback fetches, retry with the iframe `postMessage`
fallback:

```bash
python3 scripts/mdp.py open <path-to-markdown-directory> --channel sender
```

If the image payload is too large, optionally downscale/recompress before
sending:

```bash
python3 scripts/mdp.py open <path-to-markdown-directory> --max-image-width 1600 --jpeg-quality 82
```

For manual transfer, package the directory as a project ZIP:

```bash
python3 scripts/package_project.py <path-to-markdown-directory>
```

### Examples

```bash
# Open a file through the default bridge channel
python3 scripts/mdp.py open README.md

# Open a short text-only file through URL hash mode
python3 scripts/mdp.py open docs/guide.md --channel hash --no-open

# Open a directory with local images through the default bridge channel
python3 scripts/mdp.py open article-folder

# Test the bundled sample with a local image
python3 scripts/mdp.py open references/sample-with-image

# Open against a local MarkdownPoster dev server
python3 scripts/mdp.py open article-folder --base-url http://localhost:3000/import

# Use the iframe sender fallback if loopback fetch is unavailable
python3 scripts/mdp.py open article-folder --channel sender

# Downscale large PNG/JPEG images before importing
python3 scripts/mdp.py open article-folder --max-image-width 1600 --jpeg-quality 82

# Package a directory with local images for manual ZIP import
python3 scripts/package_project.py article-folder -o article.markdownposter.zip

# Use custom base URL
python3 scripts/mdp.py open content.md --base-url https://custom-instance.com/mdp/import
```

## How It Works

1. **Bridge mode** (default): start a temporary loopback endpoint, open `/import`, and let MarkdownPoster pull Markdown plus local image data.
2. **Sender mode**: open a local fallback page that sends Markdown plus images by `postMessage`.
3. **Hash mode**: encode short text-only Markdown in the URL hash.

The hash URL format is:
```
https://rrzxs.com/mdp/#mpmd=<base64-encoded-content>
```

## Script Reference

### `scripts/mdp.py`

**Arguments:**
- `open <source>` (required): Markdown file or directory containing `index.md`
- `--base-url` (optional): MarkdownPoster import URL (default: https://rrzxs.com/mdp/import)
- `--channel bridge|sender|hash` (optional): Import channel (default: `bridge`)
- `--no-open` (optional): Print the generated URL without opening a browser
- `--verbose` (optional): Print local HTTP requests for troubleshooting
- `--max-image-width` (optional): Downscale PNG/JPEG images wider than this width using macOS `sips`
- `--jpeg-quality` (optional): Recompress JPEG images using macOS `sips` quality 1-100
- `--timeout-seconds` (optional): How long the CLI waits for import acknowledgement

**When to use:**
- The Markdown references local images such as `./assets/a.png`
- The goal is one-command local preview/editing in MarkdownPoster
- The user should not manually select a ZIP file

**Important limitation:**
`mdp.py open` imports images into the browser's local image pool. It is good for
local preview/editing, but it is not a public share link. For public sharing,
use an asset hosting backend or configurable image uploader, then replace local
image references with returned public URLs before using `mdp.py open --channel hash`.

### `scripts/package_project.py`

**Arguments:**
- `source` (required): Markdown file or directory containing `index.md`
- `-o, --output` (optional): Output `.zip` path
- `--keep-inline-images` (optional): Preserve inline image placement

**When to use:**
- The content should be transferred as a portable project file
- Manual ZIP import in MarkdownPoster is acceptable

## Integration with Other Tools

This skill can be combined with other skills for enhanced workflows:

- **With `markdown-to-html`**: Convert Markdown to HTML, then open in MarkdownPoster for styled viewing
- **With `doc-coauthoring`**: Draft documentation, then preview in MarkdownPoster
- **With `frontend-design`**: Create Markdown content, then display in a beautiful web interface

## References

See `references/examples.md` for detailed integration examples and workflow patterns.

## Troubleshooting

### Common Issues

1. **File not found**: Ensure the file path is correct and the file exists
2. **Encoding errors**: The file must be UTF-8 encoded
3. **URL too long**: Very large Markdown files may exceed browser URL limits (typically > 2MB)
4. **Browser doesn't open**: Use `--print-url` flag and manually copy the URL
5. **Images missing after URL import**: URL import only carries Markdown text. Use `mdp.py open` for automatic local image import, or `package_project.py` for manual ZIP import.
6. **Bridge timeout**: Ensure MarkdownPoster is reachable and, for local testing, pass `--base-url http://localhost:3000/import`. Use `--verbose` to confirm the local payload and ACK endpoints were requested.
7. **Loopback fetch blocked**: Retry with `--channel sender`. If sender is used, the visible top-level page is the local sender shell with MarkdownPoster embedded in an iframe.
8. **Image payload too large**: Use `--max-image-width` and `--jpeg-quality`, or reduce source image sizes.

### Error Messages

- `Error: File '...' not found`: Check the file path
- `Error: Could not read '...' as UTF-8`: File encoding issue
- `Warning: File '...' may not be a Markdown file`: File extension mismatch (non-fatal)
