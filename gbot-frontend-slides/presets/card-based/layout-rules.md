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
- Deck chrome positions are fixed across the whole deck; do not let per-page layouts redefine them
- Do not show bottom-left keyboard legend in this preset
- The cover slide is the exception for the upper-left page anchor: keep page number and nav, but omit the anchor label entirely
- Chrome colors must follow the active theme tokens:
  - dark themes use light page numbers over dark stages
  - light themes switch page numbers, labels, and hover text to dark slate values

Recommended fixed positions for this preset:

- upper-left page anchor:
  - top inset: around `24px` to `32px`
  - left inset: around `72px`
- lower-right page number:
  - right inset: around `56px` to `72px`
  - bottom inset: around `20px` to `28px`

### Fixed Page Frame

Do not rely on content blocks to "remember" chrome avoidance. The page frame should be fixed in code first, then content should be rendered inside the remaining shell.

Reference pattern for this preset:

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

.slide {
  position: absolute;
  inset: 0;
}

.slide-content {
  position: absolute;
  left: var(--frame-left);
  right: var(--frame-right);
  top: calc(var(--frame-top) + var(--anchor-safe-band) + var(--anchor-title-gap));
  bottom: calc(var(--frame-bottom) + var(--footer-band-height));
  min-height: 0;
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

Frame rule:

- left-top anchor, right-bottom page number, and right-side controls are fixed chrome
- the content shell is an absolute inset box defined by frame variables
- slide archetypes may change their internal layout, but must not redefine the page frame
- the opening cover may drop the left-top anchor, but inner slides should keep it

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
- Reserve header-safe and footer-safe space before placing title, cards, or summary strips

### Composition Gravity

Treat the inner slide as a bounded composition with a real content zone, not as a document where components sit at their natural height.

The first question is not “how do I fill the space?”, but:

- should the main structure sit as a centered visual cluster?
- or should it stretch across the content band?

Allowed gravity modes:

`center-stage`

- preferred default for this preset
- the main structure forms a stable centered block below the title
- surrounding whitespace is intentional and supports the composition
- use for mechanism pages, key-judgment pages, sparse card clusters, and narrative explanation pages

`fill-band`

- use when the page is fundamentally a matrix, process surface, or dense comparison structure
- the main structure stretches across the remaining content band
- unused height is absorbed by the structure itself rather than left below it

Practical rule:

- default to `center-stage`
- switch to `fill-band` only when the page becomes stronger by behaving like a surface rather than a block

This is a composition rule, not a “make everything huge” rule:

- preserve the header hierarchy
- preserve footer-safe space
- keep internal spacing calm
- but make the chosen gravity mode explicit instead of letting the layout drift into accidental emptiness

### Top Anchor Safe Area

The upper-left page anchor owns its own band. The title block must start below that band instead of sharing the same vertical lane.

- treat the anchor as fixed deck chrome, not as part of the title block
- the title block starts after the anchor-safe band, not directly after the slide shell top padding
- do not rely on lucky line-height or smaller titles to avoid collisions

Recommended minimums for this preset:

- anchor-safe band height: `56px` to `64px`
- additional gap between anchor-safe band and title block: `20px` to `28px`
- effective title start below the slide top edge: around `96px` to `120px`

Validation rule:

- after layout, the page anchor and the top edge of the title block must remain visually separate
- a large first-line title must not pass behind the anchor text or cyan line
- if the title block becomes too tall, reduce title size or switch to two-line mode; do not collapse the anchor-safe band

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
- reserve both a header-safe area for the page anchor and a bottom safe area for the page number
- inner slide content should usually begin after the header-safe area, not immediately at the shell top padding

### Bottom Safe Area

Bottom clearance must be treated as an explicit layout budget, not an afterthought.

- the page number sits inside a reserved footer band
- content blocks, summary strips, and bottom-row cards must not enter that footer band
- the footer band includes visible breathing room above the page number, not just enough height to contain the glyphs
- do not rely on visual luck or shadows; reserve real layout space

Recommended minimums for this preset:

- footer-safe band height: `104px` to `116px`
- content bottom inset on inner slides: at least `96px`
- for pages with summary strips or dense bottom rows, prefer `112px` to `128px`

Implementation rule:

- the slide shell should include the safe area in its bottom padding, or
- the content region should subtract the safe area from its available height, or
- both, for dense pages such as the four-card summary grid
- do not model the page number as a separate lower-right exclusion box unless a preset explicitly needs that behavior

Validation rule:

- after layout, the lowest visible content edge must remain clearly above the page number block
- the page number should read as sitting inside a calm footer band, with clear space above it
- choose the footer band as part of the initial page budget so the lowest content row remains comfortably above it

## Card System

- Theme-aware cards with subtle inner top highlight
- Cyan-to-blue left accent rail as the default card rail
- Three-card pages should not always default to a single horizontal row:
  - if card copy is denser, keep the `3-column regular` row
  - if card copy is sparse but the page still needs left-to-right comparison, use `3-column centered`
  - if the page should read as three sequential structured lines, use `3-row stacked`
  - do not treat `3-row stacked` as the default fix for empty space; prefer `3-column centered` first when comparison matters
  - the compact stacked variant should keep the same card chrome, but move title/signifier to the left and explanatory copy to the right
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
- In `light-gray`, prefer border-led surfaces with transparent or near-transparent shadows; do not leave a visible gray drop-shadow block behind the cards

### Card Hover

Cards in this preset may use a subtle hover interaction, but it must stay restrained and presentation-grade.

Behavior:

- slight upward motion
- slight scale increase
- hover border switches to a gold edge in `light-gray`
- do not use loud glow, spring bounce, or large perspective tilt in this preset

Reference CSS:

```css
:root[data-theme="light-gray"] {
  --line-hover-gold: rgba(245, 158, 11, 0.44);
}

.card-panel {
  transition:
    transform var(--duration-fast) var(--ease-out-expo),
    border-color var(--duration-fast) ease,
    background var(--duration-fast) ease;
}

/* Important: cards often already receive transform from reveal selectors.
   Keep hover selector at least this specific so the hover transform wins. */
.slide.visible .card-panel:hover {
  transform: translateY(-7px) scale(1.006);
  border-color: var(--line-hover-gold);
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.97),
    rgba(248, 251, 255, 0.94)
  );
}
```

Implementation note:

- if the card is also targeted by `.slide.visible .reveal-stagger > *`, a plain `.card-panel:hover` rule may be overridden
- use `.slide.visible .card-panel:hover`, or move hover transform to a wrapper layer, so hover motion is actually visible

### Dense Card Pages

For dense pages such as the four-card summary grid:

- decide upfront whether the page is in compact-card mode or regular-card mode
- include compact-card mode in the initial vertical budget whenever the page uses a large title block plus a bottom-row card grid
- reduce card title size before shrinking body copy
- reduce inner padding and inter-block gaps before reducing line-height
- nested info blocks inside the card should also have a compact variant

### Three-Card Page Budgeting

Three-card pages need an explicit choice of reading mode before layout starts.

`3-column regular`

- use when each card has enough copy to justify a normal card height
- anchor card content from the top
- leave extra lower whitespace only if the title block is already very tall and the page still feels balanced

`3-column centered`

- use when the three cards are short, but horizontal comparison is still the page's main job
- treat the row as a centered comparison cluster
- increase card height only as needed; do not force a full-band stretch unless the page explicitly calls for it
- card internals may shift toward vertical centering, but should still preserve clear title/body hierarchy

`3-row stacked`

- use when sequential reading is more important than lateral comparison
- treat the page as three horizontal lanes rather than three side-by-side columns
- use this for sparse copy that reads like three compact statements, steps, or structured lines
- avoid this mode when the presenter is expected to compare differences across the three cards at a glance

Practical selection rule:

- ask first: “is this page about comparing three parallel ideas, or reading three compact lines in order?”
- if the answer is comparison, use one of the `3-column` variants
- if comparison remains important and the row still feels empty, switch from `3-column regular` to `3-column centered`
- only switch to `3-row stacked` when ordered reading is the better communication mode

### Four-Card Grid Budgeting

Four-card summary pages should not default to accidental content-fit height. They should explicitly choose either `center-stage` or `fill-band`.

`center-stage` mode:

- reserve the header zone first
- treat the `2 x 2` grid as a bounded summary block
- place the whole block in the visual middle of the content zone
- use when the page is still primarily narrative and the matrix acts as the summary payload

`fill-band` mode:

- reserve the header zone first
- stretch the `2 x 2` grid to fill the remaining content zone
- stretch each card to the row height
- keep copy top-aligned unless the page specifically needs a centered statement treatment

When to use:

- the page is mainly a comparison / summary matrix
- each card has short or medium copy
- the default content-fit cards would leave a large empty area below the grid

When not to use:

- the title block is unusually tall and already consumes most of the page
- one or more cards contain significantly longer copy that would make the stretched grid feel cramped
- the page includes an additional summary strip that already occupies the lower band

Preference rule:

- if both work, prefer `center-stage`
- switch to `fill-band` when the matrix should read as the page's dominant comparison surface, not just a centered summary block

### Structure Split Planning

`Structure Split` is an asymmetric archetype and should be planned that way from the start.

- the left column is a concept stack; its cards are content-fit cards, not equal-height cards by default
- the right column is the structural artifact; it may be visually larger, but its internal density must still fit the allocated content band
- do not force the left column into equal rows when the three cards have different text volumes
- when the right panel contains both a tree / code-like block and a second explanatory note row, plan the right panel with a tighter internal rhythm from the outset
- if vertical pressure appears, first reduce the right-panel tree size, note-chip density, and internal gaps before stealing space from the left concept cards
- the whole split layout should live inside the remaining content band as a flexible block, not as an unconstrained auto-growing block

### Page Budgeting

Before rendering any dense inner slide, explicitly budget the stage into three zones:

- header zone: page anchor, page title, subtitle
- content zone: the main card grid or process structure
- footer-safe zone: a full-width footer band reserved for the page number and visual breathing room

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
