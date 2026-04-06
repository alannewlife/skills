# Card Based Slide Archetypes

These archetypes define the allowed page structures for the preset.

## 1. Cover Slide

Use for opening page only.

- centered composition
- giant blue hero word
- yellow second-line title
- subtitle line below
- three small horizontal intro statements

## 2. Definition Grid

Use for "what is it" pages.

- 5 cards total
- recommended pattern: `3 + 2`
- all cards share the same language
- one or two cards may be wider, but not visually different in style
- title block should stay as wide as practical before wrapping
- card headers and body copy align from the top, not from the vertical center
- each card should include a small semantic icon in the header row

## 3. Three-Card Mechanism

Use for principle or mechanism explanation.

- 3 equal cards
- each card = one concept + short support
- cards should read like a chain, not isolated notes
- keep the card heads aligned to a common upper baseline
- each card should include a semantic icon that helps distinguish the mechanism role

## 4. Structure Split

Use for system composition or directory explanation.

- left side: short stacked concept cards
- right side: one larger structure card
- right card may contain directory tree, code-like structure, or layered explanation
- both the left stack and the right-side structural notes can use small header icons

## 5. Five-Step Flow

Use for process pages.

- 5 equal step cards in one row
- short step label + title + one short explanation
- bottom summary strip required
- steps sit high in the content band; do not vertically center the whole flow block
- step labels, titles, and copy all stack from the top edge of each card
- reserve clear separation between summary strip and page number
- step cards may keep the step marker as the primary signifier; extra header icons are optional here

## 6. Control Matrix

Use for "why controllable / how constrained" pages.

- top row: 3 principle cards
- bottom row: 4 smaller mapping cards
- keep the two rows visually related but distinct
- the whole matrix anchors upward so the first row starts close to the subtitle, not in the visual middle
- both rows should use small semantic icons to reinforce contract vs placeholder meaning

## 7. Three-Column Pipeline

Use for case-study pages.

- three columns: input / mapping / output
- middle column is emphasis column
- optional code panel in side columns
- bottom summary strip required
- pipeline columns and code panels should align from the top
- do not push main card copy to the bottom of pipeline cards
- reserve clear separation between summary strip and page number
- the three columns should use distinct semantic icons for input / mapping / output

## 8. Four-Card Value Grid

Use for concluding comparison or boundary pages.

- `2 x 2` card layout
- top row tends to express value
- bottom row tends to express limits / conditions
- left accent color may vary by content grouping and card meaning, but should still read as a small per-page semantic system rather than a rainbow of unrelated colors
- top row should begin high in the content band instead of floating downward
- each card should include a semantic icon in the header row, using consistent badge treatment

## Mapping From Page Types

Recommended mapping from page-detail template to preset archetypes:

- `封面页` -> Cover Slide
- `定义页` -> Definition Grid
- `原理拆解页` -> Three-Card Mechanism
- `结构页` -> Structure Split
- `流程页` -> Five-Step Flow
- `机制说明页` -> Control Matrix
- `案例落地页` -> Three-Column Pipeline
- `对比总结页` -> Four-Card Value Grid

## Reference Samples

Use these as structural samples when generating. They are not mandatory copy, but they give the renderer a concrete target beyond prose-only instructions.

### Sample A: Three-Card Mechanism

```md
## P3｜SKILLS 为什么成立

**标题**
为什么 Skill 能稳定工作，而不是一次性 prompt 运气

**副标题**
稳定性来自约束链，而不是运气

**页面要点**
- 定义边界
  - Skill 先定义输入契约，再定义生成规则
- 提供骨架
  - 模板提供稳定骨架，减少模型自由发挥带来的漂移
- 形成机制
  - Skill 的核心不是创意，而是约束、复用和可控性
```

Expected rendering:

- one wide title block
- three equal cards
- each card contains one concept plus one short explanation cluster

### Sample B: Five-Step Flow

```md
## P5｜SKILLS 的运行流程

**标题**
Skill 是如何把输入转成输出的

**副标题**
从读取输入到组织输出的五步链路

**页面要点**
- 读取输入
  - 识别任务上下文、输入结构与任务类型
- 加载规则
  - 读取 `SKILL.md` 中定义的规则、模板与资源
- 计算变量
  - 根据输入生成后续模板展开所需的数据
- 展开模板
  - 按占位符合同把内容放入确定位置
- 组织输出
  - 生成代码、文档或其他结构化结果

**一句话总结**
Skill 并不是“自由生成代码”，而是“按合同进行确定性拼装”。
```

Expected rendering:

- five short top-aligned step cards in one row
- one separate summary strip at the bottom

### Sample C: Four-Card Value Grid

```md
## P8｜SKILLS 的价值、边界与适用场景

**标题**
什么时候应该用 Skill，什么时候不该用

**副标题**
适合高迭代场景，不是万能替代

**页面要点**
- 输入能力
  - SKILLS 可以处理“结构化 JSON + 自然语言补充说明”的混合输入
- 适用场景
  - 在“设计文档驱动、快速验证、频繁调整”的场景里，Skill 很有优势
- 不适用场景
  - 在“CI 批量生成、强确定性、严格审计”的场景里，传统 generator 更合适
- 当前边界
  - 真后端、复杂权限、多模块联动、深度定制控件尚未覆盖
```

Expected rendering:

- `2 x 2` value grid
- top row for value / fit
- bottom row for boundary / proof
- reserve extra bottom safe area so the lower row never collides with the lower-right page number
- plan this archetype with compact-card density from the outset when the page title is long or each card contains two nested text blocks
