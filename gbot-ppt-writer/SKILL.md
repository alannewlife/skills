---
name: gbot-ppt-writer
description: Create normalized PPT page-detail markdown files from raw notes, scripts, outlines, talk drafts, or existing slide text. Use when the user wants a `页面明细.md` style document for later rendering into slides, especially when they want each page split into `页面内容与信息` and `页面风格与呈现`.
---

# Gbot PPT Page Detail Writer

Generate markdown documents that describe a slide deck page by page.

This skill does not render slides. It prepares the normalized source file that a slide-rendering skill can consume later.

## Use This Skill When

- the user wants to turn notes, prose, scripts, outlines, or a text deck into a `PPT 页面明细` document
- the user mentions `页面明细`, `page-detail`, `逐页拆解`, `逐页大纲`, or asks for a renderer-ready markdown slide spec
- the output is meant to become the single page-by-page content source for a later HTML / PPT renderer

## Output Boundary

The final markdown result should stay narrow and data-like.

Put renderer behavior in this skill, not in the generated result.

The generated result should include only:

- a top-level file title
- one short `页面明细字段 schema` section
- page sections using `## Pn｜页面名`
- within each page:
  - `### 页面内容与信息`
  - `### 页面风格与呈现`

Do not include in the generated result unless the user explicitly asks:

- renderer workflow explanations
- copy-editing policy
- fitting / overflow strategy
- HTML anchor behavior beyond the schema note
- long examples, recommended principles, or operator notes

## Required Schema

At file level, include a short schema section that only states:

- pages use `## Pn｜页面名`
- each page is split into:
  - `### 页面内容与信息`
  - `### 页面风格与呈现`
- each page must include at least:
  - `标题`
  - `副标题`
  - `页面要点`
  - `页面类型`
  - `版式建议`
  - `视觉重点`
  - `动效建议`
  - `布局强化说明`
- optional fields when needed:
  - `一句话总结`
  - `建议在 PPT 中可视化的目录结构/示意结构`

## Writing Rules

- normalize content into pages; do not render slides
- preserve the user's meaning; do not add marketing filler
- keep `副标题` short
- keep `页面要点` at least two levels when the material supports it:
  - level 1 = topic
  - level 2 = supporting detail
- keep `页面风格与呈现` specific to the page, not generic renderer policy
- if a page is overloaded, split it into more pages in the page-detail output
- if source content is sparse, still emit the required page fields and keep them concise

## Ending Page Rule

- default to adding one final ending page
- do not skip the ending page unless:
  - the user explicitly says not to include one, or
  - the source material already clearly includes a closing / ending page
- the ending page is a closing page, not a new argument page:
  - it should close the deck, not introduce fresh evidence
  - it may use a short recap, closing statement, thank-you line, or next-step handoff, depending on the source material
- the ending page must still use the normal page-detail schema:
  - `### 页面内容与信息`
  - `### 页面风格与呈现`
- when the source material has no explicit closing text, write the ending page in a restrained way that matches the deck tone instead of inventing a large new section

## Workflow

1. Read the source material and identify the natural page sequence.
2. Assign each page a concrete purpose and a page name.
3. Write `页面内容与信息` first:
   - 标题
   - 副标题
   - 页面要点
   - optional summary / structure block when useful
4. Write `页面风格与呈现` second:
   - 页面类型
   - 版式建议
   - 视觉重点
   - 动效建议
   - 布局强化说明
5. Ensure the deck has one explicit ending page unless the user or source already excludes the need for it.
6. Do a final pass to ensure every page has the minimum schema.

## Output Template

```md
# 文档标题

## 页面明细字段 schema

- 页面使用 `## Pn｜页面名` 作为页面分隔格式
- 每页固定分成两块：
  - `### 页面内容与信息`
  - `### 页面风格与呈现`
- 每页至少包含以下字段：
  - `标题`
  - `副标题`
  - `页面要点`
  - `页面类型`
  - `版式建议`
  - `视觉重点`
  - `动效建议`
  - `布局强化说明`

## P1｜页面名

### 页面内容与信息

**标题**
...

**副标题**
...

**页面要点**
- ...
  - ...

### 页面风格与呈现

**页面类型**
...

**版式建议**
...

**视觉重点**
...

**动效建议**
...

**布局强化说明**
- ...

## Pn｜结束页

### 页面内容与信息

**标题**
...

**副标题**
...

**页面要点**
- ...
  - ...

### 页面风格与呈现

**页面类型**
结束页

**版式建议**
...

**视觉重点**
...

**动效建议**
...

**布局强化说明**
- ...
```
