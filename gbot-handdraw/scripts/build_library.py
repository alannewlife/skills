#!/usr/bin/env python3
"""Build the style index and self-contained single-image gallery."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

from style_asset_paths import bucket_name, single_path

SKILL = Path(__file__).resolve().parents[1]
SOURCE = SKILL / "references" / "styles_200_reorganized.md"
STYLE_JSON = SKILL / "references" / "styles.json"
GALLERY = SKILL / "gallery" / "index.html"
ROW = re.compile(r"^\|\s*(\d{3})\s*·\s*([^|]+)\|\s*([^|]+)\|\s*(.*)\|\s*$")
HEADING = re.compile(r"^##\s+([A-G])\s+(.+)$")


def parse_styles() -> list[dict[str, str]]:
    group = ""
    items: list[dict[str, str]] = []
    for line in SOURCE.read_text(encoding="utf-8").splitlines():
        heading = HEADING.match(line)
        if heading:
            group = f"{heading.group(1)} {heading.group(2)}"
            continue
        match = ROW.match(line)
        if match:
            number, reference, generation_name, traits = (part.strip() for part in match.groups())
            items.append({"number": number, "group": group, "reference": reference,
                          "generation_name": generation_name, "traits": traits})
    return items


def image_uri(number: str) -> str:
    return f"../assets/images/individual/{bucket_name(number)}/{number}.png"


def gallery_html(styles: list[dict[str, str]]) -> str:
    total = len(styles)
    cards_by_group: dict[str, list[str]] = {group: [] for group in "ABCDEFG"}
    for style in styles:
        number = style["number"]
        group = style["group"][0]
        title = html.escape(style["generation_name"])
        reference = html.escape(style["reference"])
        traits = html.escape(style["traits"] or "以编号图片作为视觉参考")
        path = image_uri(number)
        search = html.escape(f'{number} {style["generation_name"]} {style["reference"]} {style["traits"]}'.lower())
        prompt = f"风格名称：#{number} · {style['generation_name']}。\n参考作者/风格名称：{style['reference']}。"
        prompt_html = html.escape(prompt)
        cards_by_group[group].append(
            f'<article class="style-card" data-group="{group}" data-search="{search}">'
            f'<div class="image-wrap"><img src="{path}" alt="#{number} {title}" loading="lazy" decoding="async"></div>'
            f'<div class="card-meta"><span class="number">#{number}</span><span class="group">{group}</span></div>'
            f'<strong>{title}</strong><small>{reference}</small>'
            f'<p class="prompt-text">{prompt_html}</p><button class="copy" type="button" data-copy="{prompt_html}">复制提示词</button></article>'
        )
    sections = []
    for group, cards in cards_by_group.items():
        group_styles = [style for style in styles if style["group"].startswith(group)]
        if not group_styles:
            continue
        group_title = html.escape(group_styles[0]["group"][2:].strip())
        start, end = group_styles[0]["number"], group_styles[-1]["number"]
        sections.append(
            f'<section class="collection" data-section="{group}">'
            f'<header class="chapter"><span class="chapter-letter">{group}</span><div>'
            f'<p>COLLECTION {group} · {start}—{end}</p><h2>{group_title}</h2></div></header>'
            f'<div class="gallery">{"".join(cards)}</div></section>'
        )
    section_html = "\n".join(sections)
    filters = "".join(f'<button type="button" data-filter="{g}">{g}</button>' for g in "ABCDEFG")
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>手绘风格标本册 · 001–{total:03}</title>
<style>
:root{{--paper:#eee8da;--paper-light:#f8f4ea;--ink:#20221d;--muted:#777264;--vermillion:#c94d32;--moss:#687255;--line:#c9bfaa;--shadow:0 14px 35px #332c2016}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;color:var(--ink);background:var(--paper);font-family:"Songti SC","STSong","Noto Serif CJK SC",Georgia,serif}}
body:before{{content:"";position:fixed;inset:0;pointer-events:none;opacity:.3;background-image:radial-gradient(#61594818 .7px,transparent .7px);background-size:5px 5px;mix-blend-mode:multiply}}
.masthead{{min-height:340px;padding:clamp(34px,7vw,86px) clamp(20px,6vw,90px) 40px;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:36px;align-items:end;border-bottom:1px solid var(--line);background:linear-gradient(115deg,#f8f2e5 0 68%,#d8d1bb 68%)}}
.eyebrow{{margin:0 0 18px;color:var(--vermillion);font:700 12px/1.2 ui-monospace,SFMono-Regular,monospace;letter-spacing:.18em;text-transform:uppercase}}h1{{max-width:850px;margin:0;font-size:clamp(45px,8vw,104px);font-weight:500;line-height:.9;letter-spacing:-.06em}}h1 i{{font-style:normal;color:var(--vermillion)}}
.intro{{max-width:560px;margin:28px 0 0;font-size:clamp(16px,2vw,21px);line-height:1.65;color:#4f5048}}.edition{{writing-mode:vertical-rl;padding:16px 11px;border:1px solid var(--ink);font-size:13px;letter-spacing:.16em;background:#f8f4e9;box-shadow:7px 7px 0 var(--vermillion)}}
.toolbar{{position:sticky;top:0;z-index:5;display:flex;flex-wrap:wrap;align-items:center;gap:12px;padding:14px clamp(18px,5vw,70px);background:#eee8daf2;border-bottom:1px solid var(--line);backdrop-filter:blur(16px)}}
.search{{position:relative;flex:1 1 300px}}.search input{{width:100%;height:44px;padding:0 42px 0 15px;border:1px solid var(--ink);border-radius:0;background:var(--paper-light);color:var(--ink);font:16px/1.2 inherit;outline:none}}.search input:focus{{box-shadow:4px 4px 0 var(--vermillion)}}.search span{{position:absolute;right:14px;top:11px;color:var(--muted)}}
.filters{{display:flex;gap:5px}}.filters button,.density{{min-width:38px;height:38px;border:1px solid var(--line);background:transparent;color:var(--ink);font:700 13px/1 ui-monospace,SFMono-Regular,monospace;cursor:pointer}}.filters button:hover,.filters button.active,.density:hover{{color:#fff;background:var(--ink);border-color:var(--ink)}}
.result-count{{margin-left:auto;color:var(--muted);font:12px/1 ui-monospace,SFMono-Regular,monospace}}
main{{padding:0 clamp(18px,5vw,70px) 90px}}.collection{{padding:64px 0 22px;scroll-margin-top:74px}}.collection[hidden]{{display:none}}.chapter{{display:grid;grid-template-columns:auto 1fr;gap:24px;align-items:center;margin:0 0 34px;padding:0 0 18px;border-bottom:1px solid var(--ink)}}.chapter-letter{{display:grid;place-items:center;width:72px;height:72px;background:var(--ink);color:var(--paper-light);font:500 46px/1 Georgia,serif;box-shadow:7px 7px 0 var(--vermillion)}}.chapter p{{margin:0 0 5px;color:var(--vermillion);font:700 11px/1.2 ui-monospace,SFMono-Regular,monospace;letter-spacing:.13em}}.chapter h2{{margin:0;font-size:clamp(23px,3vw,38px);font-weight:500;letter-spacing:-.03em}}.gallery{{display:grid;grid-template-columns:repeat(auto-fill,minmax(168px,1fr));gap:clamp(12px,1.6vw,22px)}}body.compact .gallery{{grid-template-columns:repeat(auto-fill,minmax(138px,1fr));gap:10px}}
.style-card{{min-width:0;transition:opacity .25s,transform .25s}}.style-card:nth-child(4n+1){{transform:rotate(-.35deg)}}.style-card:nth-child(4n+3){{transform:rotate(.35deg)}}.style-card:hover{{transform:translateY(-7px) rotate(0);z-index:1}}.style-card[hidden]{{display:none}}
.style-card{{padding:8px 8px 12px;border:1px solid var(--line);background:var(--paper-light);box-shadow:var(--shadow)}}
.image-wrap{{width:min(100%,171px);aspect-ratio:1;margin:0 auto;overflow:hidden;background:#ddd5c3;border:1px solid #b8ad98}}.image-wrap img{{width:100%;height:100%;display:block;object-fit:cover;filter:saturate(.93)}}
.card-meta{{display:flex;justify-content:space-between;align-items:center;margin:10px 2px 7px}}.number{{color:var(--vermillion);font:800 12px/1 ui-monospace,SFMono-Regular,monospace}}.group{{display:grid;place-items:center;width:20px;height:20px;border-radius:50%;background:var(--moss);color:#fff;font:700 10px/1 ui-monospace,SFMono-Regular,monospace}}.style-card strong{{display:block;margin:0 2px;font-size:14px;line-height:1.28}}.style-card small{{display:block;margin:5px 2px 0;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.prompt-text{{min-height:58px;margin:10px 2px 8px;padding-top:9px;border-top:1px dashed var(--line);white-space:pre-line;color:#5a574f;font:11px/1.5 "Songti SC","STSong",serif}}.copy{{width:100%;height:30px;border:1px solid var(--ink);background:transparent;color:var(--ink);font:700 11px/1 inherit;cursor:pointer}}.copy:hover,.copy.copied{{background:var(--ink);color:var(--paper-light)}}
.empty{{display:none;padding:80px 20px;text-align:center;color:var(--muted);font-size:20px}}.empty.show{{display:block}}
@media(max-width:700px){{.masthead{{min-height:280px;grid-template-columns:1fr;background:#f8f2e5}}.edition{{display:none}}.toolbar{{position:relative}}.filters{{order:3;width:100%;overflow-x:auto}}.result-count{{margin-left:0}}.collection{{padding-top:46px}}.chapter{{gap:16px}}.chapter-letter{{width:56px;height:56px;font-size:34px;box-shadow:5px 5px 0 var(--vermillion)}}.gallery{{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}}}}
@media(prefers-reduced-motion:reduce){{*{{scroll-behavior:auto!important;transition:none!important}}}}
</style></head>
<body><header class="masthead"><div><p class="eyebrow">Hand-drawn style field guide · {total} specimens</p><h1>手绘风格<br><i>标本册</i></h1><p class="intro">每一种画风都有自己的编号。搜索、筛选、查看提示词，然后把编号和你的主题交给 Skill。</p></div><div class="edition">零零一 — 二六一 · 离线版</div></header>
<nav class="toolbar" aria-label="画廊工具"><label class="search"><input id="search" type="search" placeholder="搜索编号、风格名或参考名" autocomplete="off"><span>⌕</span></label><div class="filters" aria-label="分类筛选"><button class="active" type="button" data-filter="all">全</button>{filters}</div><button class="density" id="density" type="button" aria-label="切换紧凑视图" title="切换紧凑视图">▦</button><span class="result-count" id="count">{total} / {total}</span></nav>
<main id="gallery" aria-live="polite">{section_html}<p class="empty" id="empty">没有找到对应风格，换个关键词试试。</p></main>
<script>
const cards=[...document.querySelectorAll('.style-card')],sections=[...document.querySelectorAll('.collection')],search=document.querySelector('#search'),count=document.querySelector('#count'),empty=document.querySelector('#empty'),filters=[...document.querySelectorAll('[data-filter]')];let active='all';
function update(){{const q=search.value.trim().toLowerCase();let visible=0;cards.forEach(card=>{{const show=(active==='all'||card.dataset.group===active)&&(!q||card.dataset.search.includes(q));card.hidden=!show;if(show)visible++}});sections.forEach(section=>section.hidden=!section.querySelector('.style-card:not([hidden])'));count.textContent=`${{visible}} / ${{cards.length}}`;empty.classList.toggle('show',visible===0)}}
search.addEventListener('input',update);filters.forEach(button=>button.addEventListener('click',()=>{{active=button.dataset.filter;filters.forEach(x=>x.classList.toggle('active',x===button));update()}}));document.querySelector('#density').addEventListener('click',()=>document.body.classList.toggle('compact'));
document.querySelectorAll('.copy').forEach(button=>button.addEventListener('click',async()=>{{try{{await navigator.clipboard.writeText(button.dataset.copy)}}catch{{const area=document.createElement('textarea');area.value=button.dataset.copy;document.body.append(area);area.select();document.execCommand('copy');area.remove()}}button.textContent='已复制';button.classList.add('copied');setTimeout(()=>{{button.textContent='复制提示词';button.classList.remove('copied')}},1200)}}));
</script></body></html>'''


def main() -> None:
    styles = parse_styles()
    numbers = [item["number"] for item in styles]
    expected = [f"{number:03}" for number in range(1, len(styles) + 1)]
    if numbers != expected:
        raise SystemExit(f"Style source must contain exactly continuous 001–{len(styles):03} entries.")
    missing = [number for number in numbers if not single_path(number).exists()]
    if missing:
        raise SystemExit(f"Missing numbered image: {missing[0]}.png")
    STYLE_JSON.write_text(json.dumps(styles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    GALLERY.parent.mkdir(parents=True, exist_ok=True)
    GALLERY.write_text(gallery_html(styles), encoding="utf-8")
    print(f"Built {len(styles)} single-image style cards.")


if __name__ == "__main__":
    main()
