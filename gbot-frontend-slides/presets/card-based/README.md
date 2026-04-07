# Card Based

这是一个固定 house preset，适合做技术讲解、机制拆解、系统结构说明这类“卡片式信息组织”的演示文稿。

它对应的是当前这套 SKILLS 技术介绍 deck 所采用的结构语言：固定 stage、信息卡片、技术标签、页码与锚点稳定存在，一页只展示一个完整画面。

## 这个 Preset 是什么

这个 preset 的核心不是“深色”，而是“卡片式信息架构”。

它的固定特征包括：

- 以卡片为主的信息组织方式
- 可切换主题色，而不是只能用单一 dark 版本
- 固定 `1920x1080` stage
- 整个 stage 缩放进视口，而不是长页面滚动
- 右侧纵向导航 pills
- 左上角页面锚点
- 右下角页码
- 强中文标题层 + mono 技术标签层

## 适用场景

适合以下内容：

- 技术介绍
- 原理拆解
- 系统结构说明
- 流程链路说明
- 案例复盘
- 价值 / 边界 / 适用场景总结

不适合的场景通常是：

- 强视觉叙事型封面故事
- 依赖大图或全屏图片表达的展示页
- 极简单句型 keynote 风格演讲稿

## 主题变体

这个 preset 应被理解为“同一结构系统 + 多个主题变体”，而不是多个完全不同模板。

当前支持：

- `dark-console`
  - 深色控制台感
  - 蓝 / 青 / 黄强调色
  - 适合技术感更强的演示
- `light-gray`
  - 冷灰蓝底
  - 白色或近白卡面
  - 适合更明亮、咨询感或产品汇报风格

规则：

- 如果 stage、卡片系统、动效语言、页型结构都不变，就应继续使用这个 preset，只切换 theme
- 只有在结构和交互模型明显变化时，才值得拆出新的 preset

## 字体加载模式

这个 preset 默认推荐更简单的 `simple-web` 字体模式：

- 主文字层：sans
- 少量强调层：serif
- 标签 / 页码 / 技术 token：mono

它参考的是这种处理思路：[32kw 示例页面](https://www.32kw.com/view/bec2ff0)

可选高级模式：

- 国内友好 CDN 模式
  - 明确需要使用特定中文 webfont 时启用
- Google 模式
  - 面向海外用户，或明确需要 Google Fonts 时使用

规则：

- 默认先用 `simple-web`
- Google 模式必须保留，不要删掉
- 具体使用哪种模式，按受众与部署环境决定

## 内容要求

这个 preset 最适合搭配已经整理好的页面明细文档使用。

推荐输入结构：

- `## Pn｜页面名` 这种 markdown 页面标题
- 页面主标题
- 页面副标题 / 概要
- 至少两层的页面要点

文本规则：

- 可见文案要忠于源文件
- 默认不要改写、扩写、润色
- 如果版面紧张，优先拆页、换页型、调密度
- 不通过擅自改文案来“塞进页面”

## 三卡页版式选择

`card-based` 里的三卡页不是只有一种固定排法。生成时要先判断内容密度和页面目标，再选版式。

允许的三卡页变体：

- `three-column-regular`
  - 经典三列横排
  - 适合中等或偏长文案
  - 目标是横向比较三条机制或三条判断
- `three-column-centered`
  - 仍然三列横排，但卡片高度明显增加，整体撑满下半屏
  - 卡内标题与正文可做视觉中轴对齐或接近中轴的居中编排
  - 适合文案较短，但仍然希望保留“横向并列比较”的页面
- `three-row-stacked`
  - 三张卡纵向堆叠，每张卡内部横向展开
  - 左侧是 icon + 标题，右侧是解释和 token
  - 适合短文案、强列表感、且页面不强调三栏横向比较时

选择原则：

- 如果三张卡的对比关系最重要，优先在两个横排变体里选，不要先跳到竖排
- 如果文案短，且普通三列横排会在卡片下方留下明显空白，优先用 `three-column-centered`
- 只有当页面更像“连续三条条目”而不是“并列三栏判断”时，才使用 `three-row-stacked`
- 竖排不是“空了就用”的兜底排法，而是有意强化顺序阅读、减弱横向比较的版式

## 画面重心方针

这个 preset 的大方针不应是“默认把所有结构撑满”，而应是“先确定主结构的视觉重心”。

默认优先级：

- 先判断页面应该是 `center-stage` 还是 `fill-band`
- 默认优先 `center-stage`
- 只有当页面天然就是矩阵、流程面板或高密度比较页时，再使用 `fill-band`

`center-stage`

- 主结构作为一个完整的视觉簇，落在标题区下方的画面中央
- 允许结构上下保留呼吸空间
- 留白是有意的构图手段，不是排版没做满
- 更适合机制解释、关键判断、案例拆解、单一结论页

`fill-band`

- 主结构拉伸并占据剩余内容带
- 额外空间优先分配给卡片阵列本身，而不是留在阵列下方
- 更适合四宫格总结页、流程页、强比较矩阵页

生成规则：

- 不要把“空白”自动理解为问题，先判断这个页面是不是需要一个稳定的中心重心
- 当页面的主体是一组卡片，但信息量并不高时，优先把它们组织成居中的结构簇，而不是机械拉满
- 当页面的主体是规则矩阵或比较面板时，再考虑 `fill-band`

## 非协商规则

1. 固定 stage 模型必须保留
   - `1920x1080`
   - 使用统一缩放
2. 不允许 slide 内部滚动
3. 页面 chrome 必须稳定
   - 右侧导航
   - 左上锚点
   - 右下页码
4. 动效必须克制
   - 轻微 reveal
   - 轻微位移 / scale / blur
   - 不做吵闹的大动效

## 固定页眉与页脚

这套模板的页眉和页脚不是“页面装饰”，而是固定 chrome 预算。

规则：

- 左上锚点和右下页码的位置在整套 deck 中保持一致
- 新页面生成时，先为页眉和页脚预留安全区，再排标题、卡片和总结条
- 不允许单页为了多塞一点内容而侵占页眉或页脚安全区

对于 `card-based`：

- 左上锚点使用固定 top / left inset
- 右下页码使用固定 right / bottom inset
- 右侧控制条使用固定 right inset 和垂直居中定位
- 内页标题块必须从锚点安全带之后开始
- 内容区必须落在固定 content shell 内，而不是靠内容自己避让 chrome

建议直接用代码固定页面框架：

```css
:root {
  --frame-top: 40px;
  --frame-right: 88px;
  --frame-bottom: 40px;
  --frame-left: 72px;
  --anchor-safe-band: 60px;
  --anchor-title-gap: 24px;
  --footer-band-height: 116px;
  --nav-right: 28px;
}

.slide-content {
  position: absolute;
  left: var(--frame-left);
  right: var(--frame-right);
  top: calc(var(--frame-top) + var(--anchor-safe-band) + var(--anchor-title-gap));
  bottom: calc(var(--frame-bottom) + var(--footer-band-height));
}

.deck-anchor {
  position: absolute;
  top: 28px;
  left: 72px;
}

.page-number {
  position: absolute;
  right: 60px;
  bottom: 22px;
}

.nav-dots {
  position: absolute;
  right: var(--nav-right);
  top: 50%;
  transform: translateY(-50%);
}
```

具体参数和验证规则统一写在：

- [layout-rules.md](./layout-rules.md)

这里的意思是：这套模板的页眉/页脚预算属于 preset 内部规则，不应散落在全局模板里。

## 需要一起阅读的文件

使用这个 preset 生成时，还应读取这些文件：

- [tokens.md](./tokens.md)
- [layout-rules.md](./layout-rules.md)
- [slide-archetypes.md](./slide-archetypes.md)

它们的分工是：

- `tokens.md`：颜色、字体、尺寸、动效 token
- `layout-rules.md`：版式和布局硬规则
- `slide-archetypes.md`：常用页型和骨架参考

如果这些文件与通用模板规则冲突，应优先以 preset 文件为准。
