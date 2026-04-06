# Card Based Layout Rules

## Stage System

- Fixed stage size: `1920x1080`
- Render one slide at a time on a fixed stage
- Scale the full stage into the viewport
- Never switch to scrollable long-page slides
- Treat the stage as a non-shrinking canvas; if it lives inside a flex parent, set `flex: 0 0 auto`
- The slide layer must not end up larger than the scaled stage box; after layout, the active slide rect should match the stage rect
- Prefer `position: absolute` for per-slide stacking inside the fixed stage rather than relying on flex layout for slide sizing
- Verify this preset at a desktop viewport such as `1280x720` before finishing

Reference logic:

```js
const scale = Math.min(
  window.innerWidth / 1920,
  window.innerHeight / 1080
);
```

Reference CSS:

```css
.stage-viewport {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.stage-scaler {
  width: 1920px;
  height: 1080px;
  flex: 0 0 auto;
  transform-origin: center center;
  transform: scale(var(--deck-scale));
  position: relative;
}
```

Validation check for this preset:

```javascript
const stage = document.querySelector('.stage-scaler');
const activeSlide = document.querySelector('.slide.active');
const stageRect = stage.getBoundingClientRect();
const slideRect = activeSlide.getBoundingClientRect();

const fitsStage =
  Math.abs(stageRect.width - slideRect.width) < 1 &&
  Math.abs(stageRect.height - slideRect.height) < 1 &&
  Math.abs(stageRect.left - slideRect.left) < 1 &&
  Math.abs(stageRect.top - slideRect.top) < 1;

if (!fitsStage) {
  console.warn('card-based stage mismatch: active slide bounds do not match stage bounds.');
}
```

## Deck Chrome

- Right-side vertical navigation pills stay in viewport coordinates, not stage coordinates
- Upper-left page anchor uses mono text and a short cyan line
- Lower-right page number stays quiet and detached from card content
- Do not show bottom-left keyboard legend in this preset
- Chrome colors must follow the active theme tokens:
  - dark themes use light page numbers over dark stages
  - light themes switch page numbers, labels, and hover text to dark slate values

## Background Language

- Atmospheric radial-gradient base tied to the active theme
- Soft accent glow in corners
- Fine grid lines and dot texture overlays
- Keep the background atmospheric but secondary
- For `light-gray`, use cool gray-blue haze instead of dark-console glow, and reduce blend intensity so the page stays bright and clean

## Slide Composition

For inner slides:

- top breathing room is explicit
- title block sits in the upper band
- content region fills the middle
- footer / summary strip, when present, sits close to the bottom but does not collide with page number
- content region should align from the top of its band, not vertically center dense card layouts
- title and subtitle should use a wide upper-band measure; avoid premature wrapping when one line still fits comfortably
- For medium-length titles, prefer a single line after widening the title measure; only allow two lines when the full upper band is genuinely exhausted

### Page Title Fitting

Use an explicit fitting rule for the in-slide page title instead of relying on prose judgment alone:

- target the page title only, not the upper-left page anchor
- try single-line first
- if the title can fit on one line at or above the single-line threshold, keep it on one line
- if single-line fitting would push the font size below the threshold, allow up to two lines
- never allow three lines for the main page title in this preset

Recommended values for this preset:

- title max width: `1480px`
- single-line max size: `82px`
- single-line threshold: `64px`
- two-line minimum size: `52px`
- line-height: around `1.08`

Reference behavior:

```js
// single-line pass
// white-space: nowrap
// binary search the largest size that fits width

if (singleLineSize >= 64) {
  useSingleLine(singleLineSize);
} else {
  // two-line pass
  // white-space: normal
  // binary search the largest size whose height stays within 2 lines
  useTwoLinesAtMost(twoLineSize);
}
```

Recommended content shell:

- top padding: around `5.4rem`
- bottom padding: around `3rem`
- left padding: around `2.7rem`
- right padding: around `3.75rem`
- title block max width: around `1500px`
- subtitle max width: around `1400px`
- reserve a bottom safe area for the page number when a footer strip / summary strip exists

### Bottom Safe Area

Bottom clearance must be treated as an explicit layout budget, not an afterthought.

- the lower-right page number owns a reserved safe area
- content blocks, summary strips, and bottom-row cards must not enter that area
- do not rely on visual luck or shadows; reserve real layout space

Recommended minimums for this preset:

- page number safe area height: `72px`
- page number safe area width: `140px`
- content bottom inset on inner slides: at least `96px`
- for pages with summary strips or dense bottom rows, prefer `112px` to `128px`

Implementation rule:

- the slide shell should include the safe area in its bottom padding, or
- the content region should subtract the safe area from its available height, or
- both, for dense pages such as the four-card summary grid

Validation rule:

- after layout, the lowest visible content edge must remain clearly above the page number block
- choose the bottom inset as part of the initial page budget so the bottom row remains comfortably above the page number block

## Card System

- Theme-aware cards with subtle inner top highlight
- Cyan-to-blue left accent rail as the default card rail
- The left accent rail is part of the preset's fixed visual language, not an optional decoration
- Use a slightly wider rail than a generic 3-4px dashboard line so cards read more clearly at presentation distance
- Recommended rail width for this preset: around `6px`
- Do not treat rail color as a decorative rotation by card index
- Use rail color to support grouping and reading structure when the content naturally splits into distinct semantic clusters
- In a mixed card set, keep one default system color for neutral / explanatory cards, then introduce additional rail colors only when they help the audience distinguish different content roles
- If a page has more than four cards, colors may still vary, but they should be shared by content groups rather than assigned one-by-one to each card
- Favor a small palette per page; too many unrelated rail colors weakens the reading hierarchy
- Cards should include a small semantic icon when the page archetype is card-driven
- The icon is part of the card header language and should sit alongside the technical tag / label, not float independently in the card body
- Icons should help scanning, not become a second headline
- Rounded corners and strong depth shadow
- Technical tags use mono text and capsule shapes
- Summary cards use a warmer yellow-tinted treatment and larger radius
- Card content should anchor to the top of the card by default; avoid vertical centering that makes cards look like they are sinking
- In dense pages, align top rows, card headers, and body copy from a shared upper baseline before using extra bottom space
- Do not bottom-anchor card copy with `justify-content: space-between` unless a specific decorative element must stay at the bottom; primary card text always starts from the top
- Card density should be chosen as part of the page plan, together with header height and bottom safe area, so the full card content fits inside the allocated content band from the start
- In `light-gray`, keep the same card geometry and rail treatment, but switch card surfaces to white / near-white panels with slate text and lighter shadows

### Dense Card Pages

For dense pages such as the four-card summary grid:

- decide upfront whether the page is in compact-card mode or regular-card mode
- include compact-card mode in the initial vertical budget whenever the page uses a large title block plus a bottom-row card grid
- reduce card title size before shrinking body copy
- reduce inner padding and inter-block gaps before reducing line-height
- nested info blocks inside the card should also have a compact variant

### Page Budgeting

Before rendering any dense inner slide, explicitly budget the stage into three zones:

- header zone: page anchor, page title, subtitle
- content zone: the main card grid or process structure
- footer-safe zone: reserved empty space for page number and visual breathing room

Planning rule:

- choose the card mode and title size while the footer-safe zone is already reserved
- do not let the content zone consume footer-safe space
- for summary grids, assume compact-card mode by default when the header title is long or the bottom row contains two nested text blocks per card

### Card Icon Language

Use icons as a fixed supporting layer for card-driven pages in this preset:

- definition cards: yes
- mechanism cards: yes
- structure cards: yes
- control / placeholder cards: yes
- pipeline cards: yes
- four-card value grid: yes
- cover slide: no mandatory icon

Placement rule:

- place the icon in the header row, next to the card label / tag
- keep the icon inside a compact badge or disc so it belongs to the card system
- align icon, tag, and card index from the same top baseline

Visual rule:

- icon size should stay small relative to the card title
- icon treatment should follow the preset accent system
- icon color may vary by card meaning, but the geometry and badge treatment should stay consistent across the deck
- never replace text labels with icons; icons are supplementary

### Rail Color Semantics

Use the rail color system as a flexible semantic layer, not as a rigid fixed lookup table.

- default informational cards:
  - usually use the preset's main blue / cyan rail
- emphasized or central cards:
  - may shift toward yellow when a card represents the key pivot, decision point, or highlighted takeaway
- risk, boundary, anti-pattern, or limitation cards:
  - may shift toward magenta / pink or a related warning hue
- proof, outcome, validation, or landed result cards:
  - may shift toward green

Generalization rule:

- always start from the default system rail
- only add alternate rail colors when the page content itself suggests real semantic grouping or contrast
- when multiple cards belong to the same semantic group, they should share the same rail color
- do not force a complete color legend on every page; some pages should stay entirely on the default rail color

Recommended compact-card adjustments:

- card title size: around `28px` to `32px`
- card inner padding: around `22px` to `28px`
- nested block padding: around `12px` to `16px`
- nested block body size: around `15px` to `16px`

## Motion Rules

- Use staged reveal classes:
  - `reveal`
  - `reveal-left`
  - `reveal-scale`
  - `reveal-blur`
- Default motion should be short and restrained
- Avoid heavy parallax, particle fields, or noisy cursor effects in this preset

## Content Density

This preset is information-dense but still presentation-first:

- cover: 1 hero word + 1 title + 1 subtitle + 3 short intro lines
- definition page: 5 cards
- mechanism page: 3 cards
- structure page: 3 short cards + 1 structure card
- flow page: 5 step cards + 1 summary strip
- control page: 3 principle cards + 4 token cards
- case page: 3 pipeline cards + 1 summary strip
- summary page: 4 cards

If a page exceeds its archetype, split the content. Do not cram.
