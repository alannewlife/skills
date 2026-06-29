# MarkdownPoster 上传技能

这个 Skill 用于把本地 Markdown 文件或 Markdown 项目目录一键打开到 MarkdownPoster 网页（rrzxs.com/mdp)中，进行预览、编辑和整理带图片的 Markdown 内容。基于网页的能力，做成海报和公众号发布。

## 适用场景

- 打开单个 Markdown 文件。
- 打开包含 `index.md` 和 `assets/` 图片目录的 Markdown 项目。
- 自动把本地图片导入浏览器本地图片池，避免手动打 ZIP 上传。
- 用本地 Markdown 内容快速测试公网 MarkdownPoster 页面。

## 图片处理方式

本地图片会在导入时读取为 `data:image/...;base64,...`，存入浏览器的本地图片池。Markdown 中的本地图片引用会改写成：

```markdown
![](local://img_xxx)
```

这样导入完成后，页面显示图片不再依赖原始磁盘路径。原图移动或删除后，当前浏览器里的 MarkdownPoster 仍然可以显示图片。

网络图片不会下载，也不会改写，会保持原始 URL。

## 常用参数

```bash
python3 scripts/mdp.py open <source> \
  --base-url https://rrzxs.com/mdp/import \
  --channel bridge \
  --timeout-seconds 30
```

- `--base-url`：MarkdownPoster 导入页地址，默认是 `https://rrzxs.com/mdp/import`。
- `--channel bridge|sender|hash`：导入通道，默认是 `bridge`。
- `--no-open`：只打印导入 URL，不自动打开浏览器。
- `--verbose`：打印本地 bridge/sender 请求，方便排查问题。
- `--max-image-width`：导入前压缩过宽的 PNG/JPEG 图片。
- `--jpeg-quality`：导入前重新压缩 JPEG 图片。
- `--timeout-seconds`：等待网页导入确认的秒数。

## 通道说明

- `bridge`：默认方式。CLI 在本机启动临时 `127.0.0.1` 服务，网页从本机拉取 Markdown 和图片 payload。
- `hash`：短文本方式。只适合无本地图片的小 Markdown 文档。
