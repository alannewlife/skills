---
name: gbot-wechat-article
description: "公众号文章写作与 Agnes Image 2.1 Flash 配图工作流。用于写公众号、推文、微信文章、把访谈/转写稿整理成公众号文章，并生成封面图/正文信息图/结尾引导图提示词；如果用户没有明确说明是否出图，先用中文询问是直接生成图片还是只提供提示词。"
---

# 公众号文章 + Agnes 配图助手

## 适用场景

当用户要：
- 写公众号文章、推文、微信文章；
- 把访谈稿、视频转写稿、资料整理成公众号文章；
- 先准备插图 Prompt 和插图位置；
- 用 Agnes Image 2.1 Flash 生成公众号配图；

使用本 skill。

## 核心原则

- 先写出可读的公众号文章，再处理配图。
- 如果用户已经明确要求“生成图片/开始画图/用 Agnes 出图/直接画出来”，默认等同于“用 Agnes Image 2.1 Flash 出图”，按要求调用 Agnes 图片生成脚本，不再追问。
- 如果用户已经明确要求“只要提示词/先不要生成图片/不要出图”，只生成文章和配图提示词，不调用出图脚本。
- 如果用户没有明确说明图片处理方式，在写文章前或最迟保存 Markdown 正文前先用中文询问：“这次配图要直接画出来，还是只提供图片提示词？”等用户选择后再继续。
- 面向用户的确认问题、状态说明和交付说明都用中文；图片生成 Prompt 仍以英文为主，只描述画面。
- 默认使用 `agnes-image-2.1-flash`，接口地址为 `https://apihub.agnes-ai.com/v1/images/generations`。
- API key 从环境变量 `AGNES_API_KEY` 或 `config/agnes.env` 读取；仓库里只保留占位，不写入真实 key。
- 不再默认调用 GPT 图片模型；只有 Agnes 不可用且用户明确要求临时 fallback 时，才考虑当前环境里的 `image_gen`。
- 输出默认保存到当前工作目录的 `outputs/`；如果用户指定路径，按用户路径保存。

## Agnes 出图配置

首次使用前，把 key 填到以下任一位置：

```bash
export AGNES_API_KEY="你的 Agnes API Key"
```

或编辑本 skill 目录下的 `config/agnes.env`：

```bash
AGNES_API_KEY=YOUR_AGNES_API_KEY_HERE
AGNES_BASE_URL=https://apihub.agnes-ai.com
AGNES_IMAGE_MODEL=agnes-image-2.1-flash
```

脚本位置：

```bash
python scripts/generate_agnes_images.py --help
```

## 必读资源

开始写作前读取：
- `writing_style.md`：公众号口吻、段落和情绪表达。
- `stages/02-title.md`：需要标题方案时读取。
- `stages/03-framework.md`：需要结构方案时读取。
- `stages/04-writing.md`：写全文时读取。

需要配图时读取：
- `image_templates/style-block.md`
- `image_templates/cover.md`
- `image_templates/infographic.md`
- `image_templates/cta.md`

## 工作流

### 1. 明确文章定位

如果用户已经给出素材和方向，直接提炼：
- 主题；
- 目标读者；
- 文章类型（观点/干货/案例/列表）；
- 核心收获；
- 期待读者动作。

如果用户只说“写一篇公众号”，再按 `stages/01-topic.md` 追问。

### 2. 标题处理

默认给 5-10 个标题候选，并推荐 1 个。

但当用户明确要求“直接写出来”“先做一版”“不用选择”时，可以直接选推荐标题继续，避免卡住流程。

### 3. 写文章

按 `writing_style.md` 和 `stages/04-writing.md` 写：
- 口语化，但不要碎片化；
- 观点清楚，有真实判断；
- 少空话，多信息；
- 适合公众号阅读，段落不要太长；
- 目标 2500-3500 中文字符，除非用户指定更长或更短。

如果素材来自访谈/转写稿：
- 不做逐字稿复刻；
- 提炼主线和观点；
- 可引用少量关键对话或细节；
- 不编造来源中没有的事实。

成稿后必须做一次轻量文字层次增强：
- 给关键判断、转折句、金句加少量“行内引用”标识；
- 行内引用格式使用反引号，例如：`担心没有用，判断才有用。`
- 不要用加粗做重点标识，避免 `**重点**`；
- 可以添加少量独立引用块，但不要堆太多，优先使用行内引用；
- 不改写文章结构，不大幅重写正文，只做轻量修饰。

### 4. 配图处理方式确认

写文章前或最迟保存 Markdown 正文前，先判断用户是否已经指定配图处理方式：

- 明确要直接出图：写文章、生成配图提示词，并在保存后默认调用 Agnes Image 2.1 Flash 出图。
- 明确只要提示词：写文章、生成配图提示词，不调用出图脚本。
- 未明确指定：先用中文提问，不要直接假设。

建议提问：

```text
这次配图要直接画出来，还是只提供图片提示词？

你可以回复：
1. 直接画出来：我会默认用 Agnes Image 2.1 Flash 生成图片并插入 Markdown。
2. 只提供提示词：我只写文章和配图 Prompt，不生成图片。
```

用户选择后再继续后续步骤。

### 5. 插图 Prompt 占位

文章完成时，同步设计配图：
- 1 张封面图；
- 2-3 张正文信息图；
- 1 张结尾引导图；
- 如文章较长，可增加到 5-6 张。

先把插图位置直接插入文章正文，用引用块占位：

```markdown
> **插图提示词｜封面图：标题**  
> Create a 900x383 horizontal WeChat article cover illustration...
```

占位块必须出现在实际建议插图位置，而不是集中放在文末。

图片尺寸按用途选择：
- 封面图/分享预览图：`900x383`，只放在文章开头或作为公众号封面使用；
- 正文插图/正文信息图：默认 `900x600`，阅读更舒适；
- 概念卡片图：可用 `900x900`，适合单个抽象概念；
- 结尾引导图：默认 `900x600`；只有需要公众号底部横幅时才用 `900x383`；
- 不要把正文插图默认做成 `900x383` 的细长横幅。

Prompt 要写给 Agnes Image 2.1 Flash：
- 英文为主，只描述画面，不要求模型生成可读文字；
- 明确尺寸，并按用途选择：封面 `900x383`，正文默认 `900x600`；
- 明确风格：warm cream paper texture, colored pencil line art, light watercolor wash；
- 默认不要让图片里出现中文、英文、数字或可读文字；需要解释的文字放在正文、图注或 Markdown alt 文本里；
- 只有用户明确要求“图片里必须有文字”时，才加入极少量文字，并提醒 Agnes 对中文渲染可能不稳定；
- 明确负面约束：no 3D, no photorealism, no dark cyberpunk, no dense text；
- 明确文字负面约束：no Chinese characters, no readable words, no captions, no labels；
- Prompt 本身只描述画面，不要包含 API key、接口地址或脚本命令。

### 6. 保存文件

保存两个 Markdown 文件：
- `<标题关键词>_article.md`：带插图 Prompt 引用块的文章。
- `<标题关键词>_image_prompts.md`：单独汇总所有图片 Prompt，方便批量检查和批量生成。

如果已经在文章中完整插入 Prompt，也仍然建议额外保存汇总文件。

`<标题关键词>_image_prompts.md` 中每张图建议同时保留一个 JSON 代码块，便于脚本直接批量读取：

````markdown
## 01-cover

```json
{
  "filename": "01-cover.png",
  "size": "900x383",
  "prompt": "A 900x383 horizontal WeChat article cover illustration..."
}
```
````

正文图示例：

````markdown
## 02-inline

```json
{
  "filename": "02-inline.png",
  "size": "900x600",
  "prompt": "A 900x600 inline WeChat article illustration..."
}
```
````

### 7. 按用户选择生成图片

只有在用户明确要求生成图片，或在第 4 步选择“直接画出来”时：
- 默认调用 `scripts/generate_agnes_images.py`，用 Agnes Image 2.1 Flash 逐张或批量生成；
- 不要把“直接画出来”解释为调用 GPT 图片模型或其他出图工具；除非用户明确要求临时 fallback，否则只使用 Agnes；
- 默认以 Base64 返回并保存为本地 PNG，避免图片 URL 过期；
- 脚本会按 `size` 自动后处理到精确像素尺寸；如需保留模型原始尺寸，传 `--resize-mode none`；
- 生成后保存图片到 `outputs/images/` 或用户指定目录；
- 将文章中的 Prompt 引用块替换为 Markdown 图片链接；
- 如果中文渲染不稳，优先生成无文字版本，并建议后期手动加字。

单张生成示例：

```bash
python scripts/generate_agnes_images.py \
  --prompt "A 900x600 inline WeChat article illustration..." \
  --filename 02-inline.png \
  --size 900x600 \
  --output-dir outputs/images
```

批量生成示例，适合读取 `<标题关键词>_image_prompts.md` 里的 JSON 代码块：

```bash
python scripts/generate_agnes_images.py \
  --batch-json outputs/标题关键词_image_prompts.md \
  --output-dir outputs/images
```

## 配图默认风格

沿用 `image_templates/` 的公众号手绘信息图风格：
- 封面图 `900x383`，正文图默认 `900x600`；
- 封面图需要中心安全区，正文图优先保证阅读舒适；
- 奶油色纸张底；
- 彩铅线稿 + 淡水彩；
- 暖色、轻涂鸦、干净；
- 默认无文字，不生成中文、英文、数字或标签；
- 不要 3D、不要摄影写实、不要复杂背景。

## 交付检查

交付前检查：
- 文章标题、结构完整；
- 关键重点已用行内引用反引号标识，没有用加粗标识重点；
- 插图 Prompt 数量与文中占位一致；
- 每个 Prompt 都包含尺寸、风格和负面约束；
- 默认图片 Prompt 不要求渲染中文或任何可读文字，除非用户明确指定；
- 没有真实 API key、`glm-image`、`cogview`、旧版 `generate_images.py` 调用；
- 如果需要出图，使用 `generate_agnes_images.py`，模型为 `agnes-image-2.1-flash`；
- 如果用户只是要 Prompt，不要生成图片。
