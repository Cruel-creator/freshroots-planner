---
name: Freshroots Planner
description: A calm, light operations dashboard where every number is one click from its evidence. White cards on a cool canvas, one green action colour, Apple-grade motion as the finish.
colors:
  brand: "#15803d"
  brand-hover: "#166534"
  brand-soft: "#e8f5ec"
  brand-ink: "#14532d"
  canvas: "#f5f6f8"
  card: "#ffffff"
  sunken: "#f9fafb"
  ink: "#111827"
  ink-2: "#4b5563"
  ink-3: "#6b7280"
  line: "#e5e7eb"
  line-soft: "#f0f1f3"
  ok: "#16a34a"
  ok-ink: "#15803d"
  ok-soft: "#e7f6ec"
  warn: "#d97706"
  warn-ink: "#b45309"
  warn-soft: "#fdf3e2"
  crit: "#dc2626"
  crit-ink: "#b91c1c"
  crit-soft: "#fdecec"
  series-slate: "#334155"
  series-teal: "#0f766e"
  series-amber: "#d97706"
  series-mist: "#94a3b8"
typography:
  kpi:
    fontFamily: "Inter Variable, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif"
    fontSize: "28px"
    fontWeight: 650
    lineHeight: 1.15
    letterSpacing: "-0.025em"
    fontFeature: "\"tnum\""
  headline:
    fontFamily: "Inter Variable, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif"
    fontSize: "24px"
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  page-title:
    fontFamily: "Inter Variable, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif"
    fontSize: "17px"
    fontWeight: 650
    letterSpacing: "-0.015em"
  title:
    fontFamily: "Inter Variable, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 600
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Inter Variable, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "-0.006em"
    fontFeature: "\"cv11\", \"ss01\""
  table:
    fontFamily: "Inter Variable, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: "\"tnum\""
  label:
    fontFamily: "Inter Variable, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif"
    fontSize: "12.5px"
    fontWeight: 500
    lineHeight: 1.45
  column-head:
    fontFamily: "Inter Variable, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif"
    fontSize: "11.5px"
    fontWeight: 600
  mono:
    fontFamily: "SF Mono, ui-monospace, Menlo, Consolas, monospace"
    fontSize: "11.5px"
rounded:
  pill: "20px"
  card: "12px"
  figure: "10px"
  control: "8px"
  tag: "6px"
spacing:
  grid-gap: "16px"
  card-x: "18px"
  card-y: "16px"
  content-x: "28px"
  content-x-mobile: "16px"
  sidebar-w: "240px"
  header-h: "60px"
components:
  button-primary:
    backgroundColor: "{colors.brand}"
    textColor: "{colors.card}"
    rounded: "{rounded.control}"
    padding: "0 14px"
    height: "34px"
  button-primary-hover:
    backgroundColor: "{colors.brand-hover}"
  button-secondary:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "0 14px"
    height: "34px"
  button-secondary-hover:
    backgroundColor: "{colors.sunken}"
  button-quiet:
    backgroundColor: "{colors.sunken}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "0 14px"
    height: "34px"
  button-danger:
    backgroundColor: "{colors.card}"
    textColor: "{colors.crit-ink}"
    rounded: "{rounded.control}"
    padding: "0 14px"
    height: "34px"
  button-danger-hover:
    backgroundColor: "{colors.crit-soft}"
  button-small:
    padding: "0 10px"
    height: "28px"
  card:
    backgroundColor: "{colors.card}"
    rounded: "{rounded.card}"
    padding: "16px 18px 18px"
  kpi-card:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink}"
    typography: "{typography.kpi}"
    rounded: "{rounded.card}"
    padding: "16px 18px"
  nav-item:
    textColor: "{colors.ink-2}"
    rounded: "{rounded.control}"
    padding: "8px 10px"
  nav-item-active:
    backgroundColor: "{colors.brand-soft}"
    textColor: "{colors.brand-ink}"
  nav-count:
    backgroundColor: "{colors.warn-soft}"
    textColor: "{colors.warn-ink}"
    rounded: "{rounded.pill}"
    padding: "1px 7px"
  input:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "8px 10px"
  tag:
    backgroundColor: "#f1f2f4"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.tag}"
    padding: "0 8px"
    height: "22px"
  tag-brand:
    backgroundColor: "{colors.brand-soft}"
    textColor: "{colors.brand-ink}"
  tag-warn:
    backgroundColor: "{colors.warn-soft}"
    textColor: "{colors.warn-ink}"
  tag-crit:
    backgroundColor: "{colors.crit-soft}"
    textColor: "{colors.crit-ink}"
  table-head:
    backgroundColor: "{colors.sunken}"
    textColor: "{colors.ink-3}"
    typography: "{typography.column-head}"
    padding: "9px 14px"
  table-cell:
    typography: "{typography.table}"
    padding: "11px 14px"
---

# Design System: Freshroots Planner

## Overview

**Creative North Star: "The Evidence Desk"**

Freshroots Planner is a light operations dashboard for a demand planner and a procurement approver. A fixed white sidebar, a frosted sticky header and a 12-column grid of white cards on a cool grey canvas carry the whole product; the planner reads the KPI row, scans the charts, opens a SKU and decides. Density and clarity come first: 14px body text, 13px tables, tabular numerals everywhere a number sits in a column, and a quiet greyscale chrome that lets the few coloured marks mean something.

Colour is rationed. Freshroots green is the one action and brand colour; red, amber and green appear only as state, and data series use slate, teal, amber and mist. Depth is a hairline border plus a barely-there two-layer shadow; nothing floats except the drawer, the toast and the mobile sidebar.

Apple applies to the motion, not the look: Lenis inertial scroll driven by the GSAP ticker, cards that rise in with a short eased stagger, numbers that count up, lines that draw on and bars that grow from zero as they enter the viewport. Every effect is skipped under reduced motion and content is visible by default. The product rejects the marketing-page look (full-bleed black bands, oversized display headlines) as firmly as the grey admin template.

**Key Characteristics:**
- 240px white sidebar with line icons, labels and pending counts; 60px frosted sticky header.
- 12-column card grid, 16px gaps, white cards with 1px borders and 12px corners.
- One row of KPI cards opens every working page.
- One green action colour; state colours only for meaning.
- Inter Variable throughout, tabular numerals for every figure.
- Motion is inertial, eased (expo-out) and once-only.

## Colors

A cool, near-neutral grey system with one saturated green for action and three state hues that only ever report a condition.

### Primary
- **Freshroots Green** (brand): primary buttons, links, text links, the brand mark, focus rings, input focus borders, the single overall sales line and the plan timeline segments. **Deep Green** (brand-hover) is its hover state. **Green Wash** (brand-soft) with **Forest Ink** (brand-ink) marks the active nav item and brand tags.

### Neutral
- **Cool Canvas** (canvas): the page ground behind cards, the frosted header tint and the drawer ground.
- **Card White** (card): cards, sidebar, inputs, secondary buttons, sheets.
- **Sunken** (sunken): table header band, quiet buttons, nav hover.
- **Ink** (ink): headings, values, body text; also the toast ground and the "info" tag.
- **Slate Ink** (ink-2): secondary text, inactive nav, field labels.
- **Muted Ink** (ink-3): sub-lines, captions, chart axis text, column heads.
- **Hairline** (line): card, input and control borders, header and sidebar rules.
- **Soft Hairline** (line-soft): row dividers inside cards, chart tracks, card footers.

### State (meaning only)
- **Critical Red** (crit, crit-ink, crit-soft): below-minimum cover, reorders, errors, rejects, worsening figures.
- **Warning Amber** (warn, warn-ink, warn-soft): pauses, pending work, exceptions, festival-month marks, nav counts.
- **Good Green** (ok, ok-ink, ok-soft): approved, healthy, target-window bands. Its text step shares the brand hex; it is used as text and tint, never as a button fill.

### Data series
- **Slate** (series-slate), **Teal** (series-teal), **Amber** (series-amber), **Mist** (series-mist): categorical series in charts, meters and donuts. Slate is the default "within window" bar.

### Named Rules
**The One Green Rule.** Freshroots Green is the only colour that fills an action. It never tells one data category from another: in-window data uses Slate, healthy states use Good Green dots and text, and the only chart it draws is the single overall sales line.

**The Meaning-Only Rule.** Red, amber and state green appear only when they report a condition the data supports; a dot, a tag tint, a bar or a value colour, never a fill behind chrome.

**The Ink-Variant Rule.** State text on white uses the -ink step (crit-ink, warn-ink, ok-ink); the bright step is for dots, bars and swatches.

## Typography

**Display Font:** none; the product has no display tier.
**Body Font:** Inter Variable (self-hosted via @fontsource-variable/inter, falling back to the system UI stack), with cv11 and ss01 on.
**Label/Mono Font:** SF Mono stack, only for inline formula code.

**Character:** One neutral grotesque at small, dense sizes, tightened slightly at weights 600 to 650 for titles and figures. Hierarchy comes from weight and ink step more than size.

### Hierarchy
- **KPI value** (650, 28px, 1.15, -0.025em, tabular): the KPI row; drops to 22px under 640px. Figure tiles use the same treatment at 24px.
- **Headline** (650, 24px, -0.025em): the welcome strip line only; 20px on phones.
- **Page title** (650, 17px, -0.015em): the header h1, paired with a 12.5px muted crumb.
- **Title** (600, 14px, -0.01em): card titles, with a 12.5px muted sub-line beneath.
- **Body** (400, 14px, 1.5, -0.006em): paragraphs capped at 72ch.
- **Table** (400, 13px, tabular in right-aligned columns): data cells; 11.5px muted sub-lines for IDs.
- **Label** (500 to 600, 12 to 12.5px, ink-3): KPI labels, notes, field labels, captions, legends.
- **Column head** (600, 11.5px, ink-3, sentence case): table headers on the sunken band.

### Named Rules
**The Tabular Rule.** Every number that can sit above or beside another number sets `font-variant-numeric: tabular-nums`: KPIs, table cells, cover values, meters, figure tiles, definition values.

**The Sentence-Case Rule.** Labels, column heads, nav and buttons are sentence case at normal tracking. Hierarchy is weight and ink, not capitals.

## Layout

The shell is a two-column grid: the 240px sidebar (sticky, full height) and a main column holding the 60px sticky header and the content well. Content pads 24px top, 28px sides, 48px bottom, capped at 1480px.

Pages are built from a 12-column grid with 16px gaps; cards take spans of 3, 4, 5, 6, 7, 8 or 12, and consecutive grids sit 16px apart. The KPI row is its own equal-column grid (six across by default, three under 1280px, two under 640px with 10px gaps).

Responsive steps: under 1100px every partial span goes full width; under 960px the sidebar becomes a 260px off-canvas panel opened from a header menu button over a scrim, and content padding drops to 16px; under 640px the header wraps, the crumb hides, the role selector fills the row, form grids go single column and charts switch to a narrow viewBox; under 600px stacking tables turn each row into a two-column labelled card.

Internal rhythm: card heads pad 16px 18px 0, bodies 14px 18px 18px, footers 11px 18px over a soft hairline. Toolbars sit 14px above their content.

## Elevation & Depth

Flat-plus-hairline. Cards are defined by a 1px border; a two-layer, 4%-opacity shadow only lifts them off the canvas. Real elevation is reserved for surfaces that cover others.

### Shadow Vocabulary
- **Resting** (`box-shadow: 0 1px 2px rgba(16,24,40,0.04), 0 1px 3px rgba(16,24,40,0.04)`): cards, KPI cards, welcome strip, secondary buttons.
- **Overlay** (`box-shadow: 0 12px 32px rgba(16,24,40,0.12)`): the SKU drawer, the toast, the off-canvas sidebar.
- **Primary lift** (`box-shadow: 0 1px 2px rgba(21,128,61,0.25)`): primary buttons only.
- **Focus halo** (`box-shadow: 0 0 0 3px rgba(21,128,61,0.15)`): focused inputs, selects and search.

### Named Rules
**The Hairline-First Rule.** A card is a border first; its shadow must stay invisible at a glance. Only the drawer, the toast and the mobile sidebar cast a visible shadow.

**The Frosted Header Rule.** Sticky bars (page header, drawer head) are canvas at 82 to 90% opacity with a 14px backdrop blur and a hairline bottom rule.

## Shapes

Gently rounded, one family: 12px for cards, sheets and the welcome strip; 10px for figure tiles and the toast; 8px for buttons, inputs, selects, nav items and the brand mark; 6px for tags; fully round for state dots, nav counts and chart tracks (8 to 10px bar ends). Chart bars use 4px tops (2px on phones). Borders are always 1px solid hairline; the only dashed lines are the target-window edges in the cover chart and the adjusted-demand rule in the SKU chart.

## Components

### Buttons
Compact and quiet.
- **Shape:** gently rounded (8px), 34px tall, 0 14px padding, 13px weight 550; small variant 28px tall, 12px.
- **Primary:** Freshroots Green with white text and the primary lift shadow; hover deepens to brand-hover.
- **Secondary:** white with a hairline border and resting shadow; hover to sunken.
- **Quiet:** sunken ground, hairline border; used for override and cancel.
- **Danger:** white with crit-ink text and a pale red border; hover fills crit-soft.
- **States:** active scales to 0.98; disabled drops to 45% opacity with a not-allowed cursor; focus is a 2px green outline offset 2px.
- **Text link:** green, 13px weight 550, underline on hover.

### Segmented control
A 3px-padded #eceef1 track (9px radius) of 12.5px buttons; the pressed segment becomes a white 7px pill with a faint shadow. Scrolls horizontally on narrow screens. Used for filters, horizons and decision choices.

### Chips / Tags and state dots
- **Tag:** 22px, 6px radius, 11.5px weight 550 on a neutral #f1f2f4 ground; tinted variants crit, warn, ok and brand use the -soft ground with -ink text; info is ink with white text.
- **State:** a 7px round dot plus 12.5px text, the default way to show recommendation and approval status in tables.

### Cards / Containers
- **Corner Style:** 12px.
- **Background:** card white on the canvas.
- **Shadow Strategy:** resting shadow (see Elevation).
- **Border:** 1px hairline.
- **Internal Padding:** head 16px 18px 0 with a 14px title and 12.5px sub-line, optional right slot; body 14px 18px 18px (or flush for tables); optional footer with a soft hairline, muted 12.5px note and a text link.

### KPI card
A card with 16px 18px padding: a 12.5px muted label (optionally led by an 8px state dot), the 28px tabular value (with an optional 14px muted unit), and a 12px note tinted by tone (crit-ink for worsening, warn-ink for attention, ok-ink for good). Values count up once on load.

### Welcome strip
The overview's opening card: white fading to #f7faf8, 26px padding, a 24px headline, a 64ch paragraph, a row of tags, and links onward bottom-right. Behind it, a faint interactive dot grid (3px dots, 20px gap, #d5dbd8 base warming to Freshroots Green near the pointer, edges faded, no click shock), omitted under reduced motion.

### Inputs / Fields
- **Style:** white, 1px hairline, 8px radius, 13.5px text, 8px 10px padding; selects and search are 34px tall. Field labels are 12px weight 600 in ink-2 above a 6px gap.
- **Focus:** border turns Freshroots Green with the 3px green focus halo.
- **Role selector:** a bordered 34px control in the header with a muted "Acting as" prefix and an inline select.

### Data tables
13px cells with 11px 14px padding and soft hairline row rules; a sticky sunken header band of 11.5px muted column heads (which sticks under the page header on tall tables); numeric columns right-aligned and tabular; clickable rows tint to #f8faf9 on hover and open the SKU drawer. Under 600px rows stack into labelled two-column cards.

### Navigation
- **Sidebar:** white, 240px, hairline right rule, 18px 14px padding. Brand lock-up (28px green 8px-radius mark with a white sprout icon, "Freshroots" 15px weight 650 over an 11px muted "Demand planning") then the nav.
- **Nav item:** 17px line icon (1.8 stroke) plus 13.5px weight 500 label, 8px 10px padding, 8px radius, ink-2; hover goes sunken with ink text; the current page takes Green Wash with Forest Ink.
- **Counts:** a right-aligned amber pill (warn-soft, warn-ink, 11px weight 600) for pending exceptions, workbench lines and signals.
- **Foot:** run ID, stock date and rule version in 12px muted text above a hairline, closing with "No purchase order leaves this app."
- **Mobile:** off-canvas under 960px with an overlay shadow and scrim; scroll locks while open.

### Header
60px, sticky, frosted canvas, hairline bottom. Page title, muted crumb (date and data window), then right-aligned role selector and the page's primary action.

### Drawer and toast
The SKU drawer slides in from the right (min(640px, 100vw)) over a 28% ink scrim with a 0.5s expo-out transform; it has a frosted sticky head and holds white sheets and figure tiles (10px radius, 24px tabular numbers). The toast is ink with white text, 10px radius, rising 20px from the bottom centre; errors switch it to crit-ink.

### Weeks-of-cover chart (signature)
Every SKU on one 0 to 24 week axis: a 170px name column (bold tabular ID plus name, green on hover, opens the SKU), an 8px rounded soft-hairline track carrying the SKU's own target window as a pale green band with dashed edges, a bar coloured by state (crit below minimum, warn above maximum or high demand, slate within window), and a right-aligned tabular value tinted crit-ink or warn-ink when out of window. Rows sort by cover ascending. Bars grow from zero with a 35ms stagger when the card scrolls into view. On phones the name column narrows to the ID.

### Charts
Data-drawn SVG on white: soft gridlines, 11px muted axis text (13px in the narrow phone viewBox), monotone curves. The overall sales line is Freshroots Green at 2.2px over a 7% green area, with festival weeks shaded in 8% amber and a ringed end dot. Donuts use 20px strokes on a soft-hairline ring with a 30px tabular centre figure. Meters are 10px rounded tracks with series-coloured fills. Legends are 12px muted text with 10px rounded swatches.

### Motion
- **Scroll:** Lenis (lerp 0.1) driven by the GSAP ticker, synced to ScrollTrigger; stopped while the mobile nav is open.
- **Entrances:** on-screen cards rise 14px and fade in over 0.7s expo-out with a 35ms stagger; cards below the fold are released by an IntersectionObserver as they enter. Content is visible by default and never held hostage by script.
- **Data:** CountUp numerals over 1.2s; lines draw on over 1.8s; bars grow over 1.1s; donut segments sweep in with an 80ms stagger; all once only.
- **UI:** 0.15s colour transitions on controls; 0.5s page fade-rise; the shared curve is `cubic-bezier(0.16, 1, 0.3, 1)`.
- **Reduced motion:** every animation, draw-on, count-up and the dot grid is skipped.

## Do's and Don'ts

### Do:
- **Do** open every working page with the header (title, crumb, role selector, primary action) and a KPI row before the card grid.
- **Do** place content in white 12px-radius cards with 1px hairline borders on the 12-column, 16px-gap grid.
- **Do** keep Freshroots Green (#15803d) for action fills, links, focus, the brand mark and the single overall sales line.
- **Do** use red, amber and state green only to report a condition, with the -ink step for text on white.
- **Do** set tabular numerals on every figure and right-align numeric table columns.
- **Do** make every number or row that has evidence open it (the SKU drawer) with one click.
- **Do** animate with the expo-out curve, once, on entry, and skip it all under reduced motion.

### Don't:
- **Don't** bring back full-bleed black bands, oversized display headlines or any marketing-page section rhythm.
- **Don't** fall back to a generic grey admin template: keep the white cards, hairlines and single green accent.
- **Don't** use Freshroots Green to tell data categories apart or to fill a control that is not an action.
- **Don't** add visible shadows to cards; elevation is for the drawer, toast and mobile sidebar.
- **Don't** set labels, column heads or buttons in uppercase or wide tracking.
- **Don't** add looping or scroll-jacked animation; motion plays once and content never waits on it.
