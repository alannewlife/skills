# Skills

这里存放的是我整理和制作的一些 Codex Skills。

这些 skills 可以单独使用，也可以按内容生产链路组合使用。当前主要分成两类：

- 公众号文章写作、配图和 Markdown 展示发布
- PPT 内容整理和 HTML 幻灯片生成

## 当前 Skill 列表

### 文章与发布预览

- `gbot-wechat-article`
  - 用于写公众号文章、推文、微信文章，也可以把访谈稿、视频转写稿、资料整理成适合公众号阅读的文章。
  - 会在正文中设计插图位置，并生成封面图、正文信息图、结尾引导图的 Agnes Image 2.1 Flash（免费的高性能生图模型） 提示词。
  - 如果没有明确说明配图方式，会先用中文询问是直接画出来，还是只提供图片提示词；选择“直接画出来”时默认使用 Agnes Image 2.1 Flash 出图。

- `gbot-markdown-poster`
  - 用于把本地 Markdown 文件或包含图片的 Markdown 目录打开到 MarkdownPoster编辑器，预览后导出海报或者公众号。
  - 适合预览、排版、分享和把本地文章快速转成更好看的 Web 阅读效果。
  - 支持本地图片导入，也可以把 Markdown 项目打包成 ZIP 供手动导入。

### PPT 与幻灯片生成

- `gbot-ppt-writer`
  - 用于把讲稿、提纲、原始文字版或已有页面文本整理成 `PPT 页面明细` Markdown 文档，供后续 renderer 使用。

- `gbot-frontend-slides`
  - 用于创建 HTML 幻灯片、优化现有页面式 PPT，以及进行 PPT/PPTX 到 HTML 的转换。

## 组合 1：公众号文章 + MarkdownPoster

`gbot-wechat-article` 和 `gbot-markdown-poster` 很适合连在一起使用，但不是强绑定关系。

常见流程是：

1. 先用 `gbot-wechat-article` 写出公众号文章，并确认配图是直接画出来，还是只提供 Prompt。
2. 如果选择直接画出来，默认用 Agnes Image 2.1 Flash 生成配图（参考 [gbot-wechat-article README](gbot-wechat-article/README.md)的API配置说明）。
3. 把生成的 Markdown 文章交给 `gbot-markdown-poster` 打开，进行预览、排版和分享。

也可以单独使用：

- 只用 `gbot-wechat-article` 写文章和准备配图提示词。
- 只用 `gbot-markdown-poster` 打开已有 Markdown 文档。

示例：

```text
/gbot-wechat-article

把这份访谈稿整理成一篇公众号文章。
文章要有标题、结构、正文，并在合适位置插入封面图、正文图和结尾引导图的提示词。
```

得到文章 Markdown 后，可以继续：

```text
/gbot-markdown-poster

打开 /Users/alan/work/xxx/文章标题_article.md 到 MarkdownPoster 里预览。
```

如果文章目录里包含本地图片，也可以直接打开整个目录：

```text
/gbot-markdown-poster

打开 /Users/alan/work/xxx/article-folder 这个目录，里面有 index.md 和 assets 图片。
```


## 执行效果示例
https://github.com/user-attachments/assets/f9c703f2-01cf-4bae-a42e-923150113ec1


<img width="1531" height="798" alt="image" src="https://github.com/user-attachments/assets/7cfc8413-0d0e-48eb-ba3a-28a976cacdfd" />

示例中直接生成的公众号文章：
https://mp.weixin.qq.com/s/iRuNFBrOzGNaIwvxdWMybQ

---

## 组合 2：PPT 页面明细 + HTML 幻灯片

`gbot-ppt-writer` 和 `gbot-frontend-slides` 是一组更偏 PPT 生产的组合，也可以单独使用。

最常见的配合方式是：

1. 先用 `gbot-ppt-writer` 把提纲或讲稿整理成标准的 `页面明细.md`
2. 再用 `gbot-frontend-slides` 基于该文档生成 HTML PPT

示例：

```text
/gbot-ppt-writer

把这份研究提纲整理成一份标准的 PPT 页面明细 markdown。
按 `## Pn｜页面名` 输出，每页都包含：
- 页面内容与信息
- 页面风格与呈现
```

得到类似：

```text
/Users/alan/work/SKILLS/SKILLS技术介绍与拆解_PPT页面明细.md
```

然后继续：

```text
/gbot-frontend-slides

用 card-based preset，light-gray 主题，读取 /Users/alan/work/SKILLS/SKILLS技术介绍与拆解_PPT页面明细.md，生成。
```

## PPT 效果示例

https://github.com/user-attachments/assets/8caf1d18-683d-44cd-8c7e-8e2d891b58e7

- [深色版](https://www.32kw.com/view/6879eb0)
- [浅色版](https://www.32kw.com/view/885e5a7)

## 升级 PPT 效果的提示词写法

可以用提示词对效果进行增强，增加图示内容。

```text
/gbot-frontend-slides

用 card-based preset，light-gray 主题，读取 XXXXXXXXXXXXXXXXX.md，生成PPT，
请在需要的地方使用svg生成内容对应的流程图、架构图、结构图等插入相应的slide，每个slide不要堆砌文字，结构布局要合理，做到信达雅。
```

<img width="804" height="454" alt="image" src="https://github.com/user-attachments/assets/6b8ff6bc-0cc7-4f40-975a-c0b0f8c8cfc0" />

- [图示版](https://rrzxs.com/slide-hermes/)
