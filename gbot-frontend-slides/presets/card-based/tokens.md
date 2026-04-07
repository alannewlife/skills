# Card Based Tokens

Use these values as the structural token contract for the preset. Keep layout, typography, and motion stable; switch the color theme via a variant token block instead of cloning the preset.

## Fonts

- Default simple-web mode, inspired by [32kw 示例页面](https://www.32kw.com/view/bec2ff0):
  - Display / Body: `Inter, system-ui, -apple-system, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif`
  - Serif accent only when needed: `"Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif`
  - Mono / Technical labels: `ui-monospace, "SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace`
- Advanced hosted modes:
  - China-friendly CDN: `LXGW Marker Gothic` + `Maple Mono CN`
  - Google: `Noto Sans SC` + `IBM Plex Mono`

Recommended loading strategy for this preset:

- default to `simple-web`
- switch to China-friendly CDN or Google only when the user explicitly wants hosted font families
- do not remove the Google mode from the preset
- use CSS stacks like:

```css
font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
font-family: "Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif;
font-family: ui-monospace, "SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
```

## Core Tokens

### `dark-console` Theme

```css
:root {
    --bg-primary: #07101d;
    --bg-secondary: #0a1628;
    --bg-tertiary: #11213c;
    --bg-panel: rgba(11, 24, 43, 0.76);
    --bg-panel-strong: rgba(16, 33, 60, 0.9);
    --bg-panel-soft: rgba(10, 18, 32, 0.62);
    --text-primary: #eff7ff;
    --text-secondary: #9db0c9;
    --text-muted: #6d829f;
    --line-soft: rgba(106, 198, 255, 0.12);
    --line-strong: rgba(106, 198, 255, 0.28);
    --accent-blue: #4ea4ff;
    --accent-cyan: #74f0ff;
    --accent-yellow: #ffe66d;
    --accent-magenta: #ff5dc8;
    --accent-green: #86ffb0;
    --shadow-deep: 0 1.5rem 4rem rgba(0, 0, 0, 0.34);
    --shadow-glow: 0 0 2rem rgba(78, 164, 255, 0.16);
}
```

### `light-gray` Theme

Use this variant when the user wants the same stage model and card system but with a cool bright gray palette, similar to light product-strategy or consulting decks.

```css
:root[data-theme="light-gray"] {
    --bg-primary: #f0f6ff;
    --bg-secondary: #f7fafe;
    --bg-tertiary: #e6eef8;
    --bg-panel: rgba(255, 255, 255, 0.78);
    --bg-panel-strong: rgba(255, 255, 255, 0.92);
    --bg-panel-soft: rgba(244, 248, 253, 0.8);
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --text-muted: #94a3b8;
    --line-soft: rgba(59, 130, 246, 0.12);
    --line-strong: rgba(30, 64, 175, 0.22);
    --line-hover-gold: rgba(245, 158, 11, 0.44);
    --accent-blue: #3b82f6;
    --accent-cyan: #0ea5e9;
    --accent-yellow: #f59e0b;
    --accent-magenta: #ec4899;
    --accent-green: #10b981;
    --shadow-deep: 0 0 0 rgba(15, 23, 42, 0);
    --shadow-glow: 0 0 2rem rgba(59, 130, 246, 0.12);
}
```

## Typography Scale

```css
:root {
    --cover-word-size: 8.35rem;
    --cover-title-size: 3.68rem;
    --cover-subtitle-size: 1.66rem;
    --cover-note-size: 0.88rem;
    --page-title-size: 4.9rem;
    --card-title-size: 2.22rem;
    --card-body-size: 1.18rem;
    --value-body-size: 1.64rem;
    --tech-size: 1rem;
    --anchor-size: 0.88rem;
}
```

## Shape And Spacing

```css
:root {
    --radius-panel: 1.5rem;
    --radius-value: 2.75rem;
    --slide-padding: 2.45rem;
    --content-gap: 0.95rem;
    --element-gap: 0.8rem;
    --cover-shell-max: 1680px;
    --page-title-max: 1320px;
    --page-lead-max: 1680px;
}
```

## Motion

```css
:root {
    --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
    --duration-fast: 0.34s;
    --duration-normal: 0.78s;
    --duration-slow: 1.2s;
}
```
