# Gbot Frontend Slides

`gbot-frontend-slides` 是一套用于生成 HTML 演示文稿的 skill。它既支持从零创建 deck，也支持把 `.pptx` 转成网页幻灯片。

这份 `README.md` 面向人类使用者和维护者；运行时真正驱动 agent 行为的是 [SKILL.md](/Users/alan/work/SKILLS/.agents/skills/gbot-frontend-slides/SKILL.md)。

项目源代码参考自：[zarazhangrui/frontend-slides](https://github.com/zarazhangrui/frontend-slides)

## 文档分工

- [SKILL.md](/Users/alan/work/SKILLS/.agents/skills/gbot-frontend-slides/SKILL.md)：执行协议。定义工作流、阶段、硬规则、何时读取哪些 supporting files。
- [README.md](/Users/alan/work/SKILLS/.agents/skills/gbot-frontend-slides/README.md)：人类说明。说明这套 skill 是什么、怎么安装、怎么用、包含什么文件、适合什么场景。

一句话：

- `SKILL.md` 回答“agent 该怎么做”
- `README.md` 回答“人该怎么理解和使用它”

## 这套 Skill 做什么

它的目标是生成“单文件、零依赖、浏览器可直接运行”的 HTML PPT。

主要能力：

- 从零生成 HTML presentation
- 把 PowerPoint 拆解后转成 HTML deck
- 支持风格预览与风格选择
- 支持固定 house preset
- 支持部署到 URL
- 支持导出 PDF

## 核心特征

- 零依赖：输出是单个 HTML 文件，CSS / JS 内联
- 视觉先行：通过生成预览帮助用户选风格，而不是先抽象描述
- 避免 AI 套路感：强调定制感和清晰视觉方向
- 生产可用：可部署、可导出、代码结构清楚
- 默认简单字体模式：正文 sans、强调 serif、标签 mono；同时保留 CDN 和 Google 作为可选高级模式

## 使用方式

### 1. 新建一份演示文稿

```text
/gbot-frontend-slides

我想做一个 AI 产品介绍 deck
```

执行流程一般是：

1. 收集内容和用途
2. 选择风格路径
3. 如果不是固定 preset，则先生成若干视觉预览
4. 生成完整 deck
5. 根据需要部署或导出 PDF

### 2. 转换 PowerPoint

```text
/gbot-frontend-slides

把 presentation.pptx 转成网页幻灯片
```

执行流程一般是：

1. 提取 PPT 中的文字、图片、备注
2. 让用户确认内容
3. 选择风格或固定 preset
4. 生成 HTML 演示文稿

### 3. 使用固定 preset

如果你不想先看 3 个风格预览，而是直接使用固定 house preset，可以在需求里明确写出 preset 名和主题。

例如：

```text
/gbot-frontend-slides

用 card-based preset，dark-console 主题，基于页面明细生成 HTML PPT
```

再比如：

```text
/gbot-frontend-slides

用 card-based preset，light-gray 主题，读取这份页面说明文档生成单文件 HTML
```

推荐写法：

- 先说明使用 `card-based` preset
- 再说明主题，如 `dark-console` 或 `light-gray`
- 如果有页面明细文档，直接把文档路径一起给出
- 如果有字体要求，也一并说明使用 `simple-web`、国内友好 CDN 或 Google 模式

一个完整示例：

```text
/gbot-frontend-slides

用 card-based preset，dark-console 主题，simple-web 字体模式，读取 /path/to/page-spec.md，生成单文件 HTML PPT，不参考现有成品
```

- 两种风格效果
<img width="1200" height="681" alt="image" src="https://github.com/user-attachments/assets/5ac61752-2360-478e-9415-e81a44ecf6e5" />

<img width="1200" height="689" alt="image" src="https://github.com/user-attachments/assets/228c4366-a2b2-4916-966b-d6ab4804aa33" />


### 4. 结合 `gbot-ppt-writer` 一起用

这两个 skill 很适合串起来：

- `gbot-ppt-writer` 负责把原始提纲、讲稿、笔记整理成标准 `页面明细.md`
- `gbot-frontend-slides` 负责读取这份页面明细，渲染成 HTML PPT

适合场景：

- 你手里只有提纲、口播稿、研究笔记，还没有逐页 slide spec
- 你希望先把内容结构定清楚，再进入视觉和 HTML 生成
- 你想让“内容整理”和“页面渲染”分成两个稳定步骤

推荐 workflow：

1. 先用 `gbot-ppt-writer` 生成页面明细
2. 再把生成的 `.md` 文件交给 `gbot-frontend-slides`

第一步示例：

```text
/gbot-ppt-writer

把这份研究提纲整理成一份标准的 PPT 页面明细 markdown。
按 `## Pn｜页面名` 输出，每页都包含：
- 页面内容与信息
- 页面风格与呈现

要求保留原始论点，不要写成营销文案。
```

预期产物通常会是类似这样的文件：

```text
/path/to/Citrini_Hormuz_PPT页面明细.md
```

第二步示例：

```text
/gbot-frontend-slides

用 card-based preset，light-gray 主题，读取 /path/to/Citrini_Hormuz_PPT页面明细.md，生成单文件 HTML PPT，不参考现有任何既有结果 PPT。
```

如果你希望把这套串联写得更完整一点，可以直接这样下指令：

```text
先用 /gbot-ppt-writer 把这份提纲整理成标准的 `页面明细.md`，
再用 /gbot-frontend-slides 基于该文档生成 HTML PPT。

渲染时使用 card-based preset，light-gray 主题，输出单文件 HTML。
```

实践建议：

- `gbot-ppt-writer` 的输出尽量保持“逐页、结构化、数据化”，不要在文档里混入太多渲染器说明
- `gbot-frontend-slides` 阶段再决定 preset、主题、字体模式、是否导出 PDF
- 如果 deck 后续会反复改，优先把 `页面明细.md` 作为单一内容源维护

## 字体加载模式

这套 skill 默认使用更简单的字体处理方式，并保留 hosted font 作为可选模式。

参考方向：

- [32kw 示例页面](https://www.32kw.com/view/bec2ff0)
- 它的处理思路很简单：
  - 主文字层：一套 sans
  - 少量强调层：一套 serif
  - 标签 / 元信息：一套 mono
  - 不把正文、标题、标签拆成很多外部字体来源

### 模式 A：`simple-web`，默认推荐

适合：

- 需要最稳妥、最省心的网页字体策略
- 希望本地预览、静态托管、截图、PDF 导出都尽量一致
- 不想把问题复杂化到外部字体加载

推荐做法：

- 主文字层：`Inter, system-ui, -apple-system, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif`
- 强调 serif 层：`"Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif`
- mono 层：`ui-monospace, "SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace`

### 模式 B：国内友好 CDN

适合：

- 面向中国大陆观众
- 明确想使用字图这类 CDN 提供的具体中文字体

### 模式 C：Google

适合：

- 观众主要在海外
- 明确需要 Google Fonts
- 所选字体栈本来就以 Google 托管字体为主

规则：

- 默认先用 `simple-web`
- Google 模式必须保留在 skill 里，不能被删掉
- 具体使用哪种模式，应按受众与部署环境决定

## 主要文件说明

| 文件 | 作用 | 什么时候读 |
| --- | --- | --- |
| [SKILL.md](/Users/alan/work/SKILLS/.agents/skills/gbot-frontend-slides/SKILL.md) | 主工作流和硬规则 | 调用 skill 时 |
| [STYLE_PRESETS.md](/Users/alan/work/SKILLS/.agents/skills/gbot-frontend-slides/STYLE_PRESETS.md) | 通用风格预设清单 | 风格选择阶段 |
| [viewport-base.css](/Users/alan/work/SKILLS/.agents/skills/gbot-frontend-slides/viewport-base.css) | 视口适配硬约束 | 生成阶段 |
| [html-template.md](/Users/alan/work/SKILLS/.agents/skills/gbot-frontend-slides/html-template.md) | HTML 结构和 JS 骨架 | 生成阶段 |
| [animation-patterns.md](/Users/alan/work/SKILLS/.agents/skills/gbot-frontend-slides/animation-patterns.md) | 动效参考库 | 生成阶段 |
| [presets/](/Users/alan/work/SKILLS/.agents/skills/gbot-frontend-slides/presets) | 固定 house preset 定义 | 选定 preset 时 |
| [scripts/extract-pptx.py](/Users/alan/work/SKILLS/.agents/skills/gbot-frontend-slides/scripts/extract-pptx.py) | 提取 PPT 内容 | PPT 转换时 |
| [scripts/deploy.sh](/Users/alan/work/SKILLS/.agents/skills/gbot-frontend-slides/scripts/deploy.sh) | 部署到 URL | 分享阶段 |
| [scripts/export-pdf.sh](/Users/alan/work/SKILLS/.agents/skills/gbot-frontend-slides/scripts/export-pdf.sh) | 导出 PDF | 分享阶段 |

## Fixed House Preset

当前这套 skill 内置的固定 house preset 包括：

- `card-based`

它实际上已经被整理成“同一结构系统 + 多主题变体”的方向，适合：

- 固定 `1920x1080` stage
- 一次只显示一页
- 技术讲解 / 机制拆解 / 系统结构页
- 卡片化信息组织

## 安装

如果你要把它装到 Claude Code 的 skill 目录：

```bash
mkdir -p ~/.claude/skills/gbot-frontend-slides/scripts

cp SKILL.md STYLE_PRESETS.md viewport-base.css html-template.md animation-patterns.md ~/.claude/skills/gbot-frontend-slides/
cp scripts/extract-pptx.py ~/.claude/skills/gbot-frontend-slides/scripts/
cp -R presets ~/.claude/skills/gbot-frontend-slides/
```

## 交付与分享

### 部署到 URL

用这个脚本部署：

```bash
bash scripts/deploy.sh ./my-deck/
```

或：

```bash
bash scripts/deploy.sh ./presentation.html
```

### 导出 PDF

用这个脚本导出：

```bash
bash scripts/export-pdf.sh ./my-deck/index.html
```

或：

```bash
bash scripts/export-pdf.sh ./presentation.html ./output.pdf
```

## 依赖要求

- Claude Code
- PPT 转换时：Python + `python-pptx`
- 部署时：Node.js + Vercel 账号
- 导出 PDF 时：Node.js，Playwright 会自动安装

## 维护建议

- 流程变化优先改 `SKILL.md`
- 面向人的解释优先改 `README.md`
- 结构骨架改 [html-template.md](/Users/alan/work/SKILLS/.agents/skills/gbot-frontend-slides/html-template.md)
- 视口安全约束改 [viewport-base.css](/Users/alan/work/SKILLS/.agents/skills/gbot-frontend-slides/viewport-base.css)
- 动效语言改 [animation-patterns.md](/Users/alan/work/SKILLS/.agents/skills/gbot-frontend-slides/animation-patterns.md)
- 固定 preset 的视觉语言改 `presets/` 下对应文件

## License

MIT。可以修改、分发、发布；保留原版权和许可声明即可。
