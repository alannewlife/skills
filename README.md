# Skills

这里存放的是我整理和制作的一些 Skills。

## 当前 Skill 列表
- `gbot-ppt-writer`
  - 用于把讲稿、提纲、原始文字版或已有页面文本整理成 `PPT 页面明细` markdown 文档，供后续 renderer（gbot-frontend-slides） 使用。
- `gbot-frontend-slides`
  - 用于创建 HTML 幻灯片、优化现有页面式 PPT，以及进行 PPT/PPTX 到 HTML 的转换。

## 组合使用示例

这两个 skill 最常见的配合方式是：

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

## 效果（两种色调主题）


https://github.com/user-attachments/assets/8caf1d18-683d-44cd-8c7e-8e2d891b58e7

- [深色版](https://www.32kw.com/view/6879eb0)
- [浅色版](https://www.32kw.com/view/885e5a7)


## 升级效果的提示词写法
可以用提示词，对效果进行增强，增加图示内容。

```text
/gbot-frontend-slides

用 card-based preset，light-gray 主题，读取 XXXXXXXXXXXXXXXXX.md，生成PPT，  
请在需要的地方使用svg生成内容对应的流程图、架构图、结构图等插入相应的slide，每个slide不要堆砌文字，结构布局要合理，做到信达雅。
```
<img width="804" height="454" alt="image" src="https://github.com/user-attachments/assets/6b8ff6bc-0cc7-4f40-975a-c0b0f8c8cfc0" />

- [图示版](https://rrzxs.com/slide-hermes/)

