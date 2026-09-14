# gbot-handdraw

一个基于编号选择手绘风格的 Codex Skill，收录 001–261 种风格。用户可以先在离线画廊中浏览图片和风格索引，再用“编号 + 主题”生成中英文生图提示词；明确要求生图时，Skill 会根据模型能力决定是否传入对应编号的参考图。

## 使用方法

浏览 `gallery/index.html`，选择一个编号，然后输入：

```text
041号风格，主题：秋天的第一杯奶茶
```

画廊支持：

- A–G 大分类浏览
- 按编号、风格名称或参考名称搜索
- 查看完整核心视觉特征
- 一键复制带主题占位的提示词模板

## 目录结构

```text
gbot-handdraw/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── assets/images/individual/
│   ├── 001-200/
│   └── 201-400/
├── gallery/
│   └── index.html
├── references/
│   ├── styles_200_reorganized.md
│   ├── styles.json
│   ├── attribution.json
│   └── model_capabilities.json
└── scripts/
```

图片资源只保留每个编号对应的一张单图，画廊展示和生图参考共用同一套文件。当前图片的宽、高已缩至原图的三分之一，以减少 Skill 体积。

## 本版本调整

- 将原仓库根目录中的风格文档与图片整理为自包含 Skill。
- 移除固定盘符和仓库外部路径，全部使用 Skill 内相对路径。
- 移除重复的合集图和四宫格参考图，仅保留 261 张编号单图。
- 重新设计离线 HTML 画廊，并保留原有 A–G 分类方式。
- 将原始文档中的生图名称、参考名称和核心视觉特征纳入画廊。
- 修复并简化资源解析、画廊构建和验证脚本。

## 原始出处

本 Skill 的风格资料和原始图片来自：

- [yang0/handraw-style](https://github.com/yang0/handraw-style) — 手绘风格编号画廊与双语提示词 Skill

本目录是在原始项目基础上进行的结构整理、资源压缩和画廊界面改版。作者与风格来源信息保留在 `references/attribution.json` 和 `references/styles_200_reorganized.md` 中。

原始仓库当前未提供明确的许可证文件；复用或再分发相关内容时，请同时查看原始项目的最新说明并尊重相应作者及素材来源。
