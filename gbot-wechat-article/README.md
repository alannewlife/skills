# WeChat Article Image Skill

这个 skill 用来写公众号文章，并为文章生成配图。当前版本的图片生成后端是 Agnes Image 2.1 Flash。

默认流程是：

1. 先写文章或整理文章。
2. 如果用户没有明确说明，先用中文询问：配图是直接画出来，还是只提供图片提示词。
3. 在合适位置插入配图提示词。
4. 如果用户选择直接出图，默认用 Agnes Image 2.1 Flash 生成图片并插入 Markdown。
5. 图片保存到当前工作目录的 `outputs/images/`。
6. 文章保存为 Markdown。

如果用户已经明确说“直接画出来”“生成图片”，就不再追问，默认用 Agnes Image 2.1 Flash 出图；如果用户明确说“只要提示词”“先不要生成图片”，就只输出文章和配图 Prompt。

## 重要：不要分享自己的 API Key

如果你要把这个 skill 发给别人，不要把下面这个文件发出去：

```text
config/agnes.env
```

这个文件是本地私有配置，里面应该放你自己的 Agnes API key。

可以分享这个模板文件：

```text
config/agnes.env.example
```

朋友拿到 skill 后，让他自己复制模板并填写自己的 key。

## 去哪里拿 Agnes API Key

1. 打开 Agnes AI 平台：

   ```text
   https://platform.agnes-ai.com
   ```
   PS: 这个平台的API目前都是免费开放使用。

2. 注册或登录账号。

3. 进入开发者控制台，找到 API Key / 密钥管理相关页面。

4. 创建一个新的 API Key。

5. 复制这个 key，保存到本地配置文件里。

Agnes 官方快速开始文档：

```text
https://agnes-ai.com/zh-Hans/docs/quickstart
```

Agnes Image 2.1 Flash 文档：

```text
https://agnes-ai.com/zh-Hans/docs/agnes-image-21-flash
```

## 配置 API Key

在 skill 目录下复制示例配置：

```bash
cp config/agnes.env.example config/agnes.env
```

然后编辑 `config/agnes.env`：

```bash
AGNES_API_KEY=把你的_Agnes_API_Key_放这里
AGNES_BASE_URL=https://apihub.agnes-ai.com
AGNES_IMAGE_MODEL=agnes-image-2.1-flash
```

也可以不用配置文件，直接设置环境变量：

```bash
export AGNES_API_KEY="把你的_Agnes_API_Key_放这里"
```

## 测试出图

在 skill 目录下执行：

```bash
python scripts/generate_agnes_images.py \
  --prompt "A warm cream paper texture illustration, colored pencil line art, light watercolor wash, no text, no readable words." \
  --filename test.png \
  --output-dir outputs/images \
  --size 900x600
```

成功后会看到类似输出：

```text
saved outputs/images/test.png
```

## 图片规则

这个模型对中文文字渲染不稳定，所以当前 skill 的默认规则是：

- 图片里不生成中文。
- 图片里也尽量不生成英文、数字、标签或其他可读文字。
- 需要解释的内容放在正文、图注或 Markdown 图片 alt 文本里。
- 封面图/分享预览图用 `900x383`。
- 正文图和结尾图优先用 `900x600`，阅读体验更好。
- 不要把正文图默认做成 `900x383` 的细长横幅。

如果确实要在图片里加字，建议后期用设计工具手动加。

## 常用命令

单张图片：

```bash
python scripts/generate_agnes_images.py \
  --prompt "A 900x600 inline article illustration, no text, warm cream paper texture, colored pencil line art." \
  --filename image.png \
  --output-dir outputs/images \
  --size 900x600
```

从 Markdown 里的 JSON prompt 批量生成：

```bash
python scripts/generate_agnes_images.py \
  --batch-json outputs/article_image_prompts.md \
  --output-dir outputs/images
```

保留 Agnes 原始返回尺寸，不做自动裁切缩放：

```bash
python scripts/generate_agnes_images.py \
  --prompt "A simple illustration, no text." \
  --filename raw.png \
  --output-dir outputs/images \
  --size 900x600 \
  --resize-mode none
```

## 发布给朋友前检查

发布前建议检查：

```bash
find . -name "agnes.env" -print
```

如果输出里有：

```text
./config/agnes.env
```

不要把它打包给别人。

只分享代码、模板和说明即可。朋友需要自己去 Agnes 平台申请 key。
