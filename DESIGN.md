---
name: Freshroots Planner
description: The Planning Brief. A weekly bulletin for a fresh-food business, set on grained oat paper in an editorial serif, with hairline rules instead of boxes. Moss is the only colour that acts; brick means running short, ochre means too much, and both always come with words.
colors:
  paper: "#f5f1e8"
  paper-2: "#efe9dc"
  paper-3: "#e7dfcc"
  sheet: "#fbf9f4"
  ink: "#1d1b17"
  ink-2: "#45413a"
  muted: "#736c5c"
  faint: "#a59d8c"
  rule: "#e0d8c6"
  rule-strong: "#c9bfa9"
  chart-bar: "#cdc3ad"
  moss: "#3b5a2b"
  moss-deep: "#2e4721"
  moss-wash: "#e7ecdc"
  brick: "#a3412b"
  brick-wash: "#f4e1d9"
  ochre: "#8f6210"
  ochre-dot: "#b8862a"
  ochre-wash: "#f3e8cf"
typography:
  front-headline:
    fontFamily: "Newsreader Variable, Iowan Old Style, Georgia, serif"
    fontSize: "clamp(2.4rem, 1.3rem + 3.2vw, 4.1rem)"
    fontWeight: 400
    lineHeight: 1.02
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Newsreader Variable, Iowan Old Style, Georgia, serif"
    fontSize: "clamp(1.9rem, 1.2rem + 2vw, 2.9rem)"
    fontWeight: 400
    lineHeight: 1.06
    letterSpacing: "-0.022em"
  figure:
    fontFamily: "Newsreader Variable, Iowan Old Style, Georgia, serif"
    fontSize: "40px"
    fontWeight: 400
    lineHeight: 1.05
    letterSpacing: "-0.02em"
    fontFeature: "\"lnum\", \"tnum\""
  section-head:
    fontFamily: "Newsreader Variable, Iowan Old Style, Georgia, serif"
    fontSize: "30px"
    fontWeight: 400
    lineHeight: 1.1
    letterSpacing: "-0.015em"
  wordmark:
    fontFamily: "Newsreader Variable, Iowan Old Style, Georgia, serif"
    fontSize: "26px"
    fontWeight: 500
    lineHeight: 1
    letterSpacing: "-0.01em"
  section-title:
    fontFamily: "Newsreader Variable, Iowan Old Style, Georgia, serif"
    fontSize: "22px"
    fontWeight: 400
    lineHeight: 1.2
    letterSpacing: "-0.012em"
  subtitle:
    fontFamily: "Newsreader Variable, Iowan Old Style, Georgia, serif"
    fontSize: "20px"
    fontWeight: 400
    lineHeight: 1.25
    letterSpacing: "-0.01em"
  lede:
    fontFamily: "Newsreader Variable, Iowan Old Style, Georgia, serif"
    fontSize: "17.5px"
    fontWeight: 400
    lineHeight: 1.55
  margin-note:
    fontFamily: "Newsreader Variable, Iowan Old Style, Georgia, serif"
    fontSize: "16px"
    fontWeight: 400
    fontStyle: "italic"
    lineHeight: 1.5
  body:
    fontFamily: "Instrument Sans Variable, ui-sans-serif, system-ui, Segoe UI, sans-serif"
    fontSize: "14.5px"
    fontWeight: 400
    lineHeight: 1.6
  table:
    fontFamily: "Instrument Sans Variable, ui-sans-serif, system-ui, Segoe UI, sans-serif"
    fontSize: "13.5px"
    fontWeight: 400
    fontFeature: "\"lnum\", \"tnum\""
  label:
    fontFamily: "Instrument Sans Variable, ui-sans-serif, system-ui, Segoe UI, sans-serif"
    fontSize: "13px"
    fontWeight: 500
  small-caps:
    fontFamily: "Instrument Sans Variable, ui-sans-serif, system-ui, Segoe UI, sans-serif"
    fontSize: "11.5px"
    fontWeight: 600
    letterSpacing: "0.08em"
    textTransform: "uppercase"
  mono:
    fontFamily: "ui-monospace, SF Mono, Menlo, Consolas, monospace"
    fontSize: "12px"
rounded:
  control: "3px"
  tag: "2px"
  dot: "50%"
spacing:
  measure: "1200px"
  gutter: "40px"
  gutter-narrow: "18px"
  section-bar-h: "46px"
  column-gap: "48px"
  row-gap: "40px"
  section-top: "44px"
  section-indent: "152px"
  colophon-top: "64px"
components:
  button-primary:
    backgroundColor: "{colors.moss}"
    textColor: "{colors.sheet}"
    rounded: "{rounded.control}"
    padding: "0 16px"
    height: "36px"
  button-primary-hover:
    backgroundColor: "{colors.moss-deep}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "0 16px"
    height: "36px"
  button-secondary-hover:
    backgroundColor: "{colors.paper-2}"
  button-quiet:
    backgroundColor: "{colors.paper-2}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "0 16px"
    height: "36px"
  button-quiet-pressed:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
  button-danger:
    backgroundColor: "transparent"
    textColor: "{colors.brick}"
    rounded: "{rounded.control}"
    padding: "0 16px"
    height: "36px"
  button-danger-hover:
    backgroundColor: "{colors.brick-wash}"
  button-small:
    padding: "0 12px"
    height: "30px"
  section:
    textColor: "{colors.ink}"
    typography: "{typography.section-title}"
    padding: "12px 0 0"
  figure-strip:
    textColor: "{colors.ink}"
    typography: "{typography.figure}"
    padding: "16px 20px"
  section-tab:
    textColor: "{colors.ink-2}"
    typography: "{typography.label}"
  section-tab-active:
    textColor: "{colors.ink}"
  input:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "8px 10px"
  tag:
    backgroundColor: "{colors.paper-2}"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.tag}"
    padding: "0 8px"
    height: "22px"
  tag-crit:
    backgroundColor: "{colors.brick-wash}"
    textColor: "{colors.brick}"
  tag-warn:
    backgroundColor: "{colors.ochre-wash}"
    textColor: "{colors.ochre}"
  tag-ok:
    backgroundColor: "{colors.moss-wash}"
    textColor: "{colors.moss-deep}"
  table-head:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.muted}"
    padding: "10px 12px 8px"
  table-cell:
    textColor: "{colors.ink-2}"
    typography: "{typography.table}"
    padding: "13px 12px"
  margin-note:
    backgroundColor: "{colors.moss-wash}"
    textColor: "{colors.ink-2}"
    padding: "14px 16px"
---

# Design System: Freshroots Planner

## Overview

**Creative North Star: "The Planning Brief"**

Freshroots Planner is a weekly bulletin for a fresh-food business, not a dashboard. Each week is an issue: a masthead with the wordmark "Freshroots *Planning Brief*", an issue line ("No. 42 · 17 October 2026") and a double ink rule, then a sticky section bar that reads like a newspaper's section index. The planner (Raghav) and procurement read it; they do not monitor it.

The front page states the week's call as a sentence ("Reorder three products. The first runs out on 24 October."), backs it with a lede, a docket of what is on Raghav's desk, and one moss action. Below it, evidence is set the way a paper sets it: a pull-quote for the exception a person must judge, numbered sections (01 The runway, 02 How demand moved), charts labelled in place, an italic caption, a moss-washed margin note and a colophon.

The ground is warm oat paper with a faint SVG grain; type is ink, not black. An editorial serif (Newsreader) carries everything that is read: headlines, ledes, figures, section titles, captions, margin notes. A quiet sans (Instrument Sans) carries everything that is operated: tabs, buttons, tables, labels, forms. Structure is drawn with hairline rules, never boxes or shadows; the only surface that floats is the product drawer.

Motion is almost absent. Scrolling is native, a page settles in with a 0.24s fade, the drawer slides in over 0.26s, and nothing animates data, follows the pointer or loops.

**Key Characteristics:**
- Masthead with serif wordmark, italic issue line and a double ink rule; sticky 46px section bar with counts and a "Reading as" role picker.
- Every headline states the finding in a sentence; a serif lede explains it.
- Grained oat paper, ink type, hairline rules instead of cards; no shadows on the page.
- One action colour (moss). Brick reports running short, ochre reports too much, always with words.
- Newsreader for reading, Instrument Sans for operating; lining tabular numerals on every figure.
- The runway: run-out dates on a calendar, not weeks of cover on a bar chart.
- Motion is a fade and a slide; nothing loops.

## Colors

A warm paper-and-ink palette with three meaningful hues. Neutrals are all oat and umber; there is no cool grey anywhere.

### Paper and ink
- **Oat Paper** (paper): the page ground, always with the grain overlay; also the ground of every sticky surface (section bar, runway axis, sticky table heads, drawer and drawer head) so they read as the same sheet.
- **Paper 2** (paper-2): hover ground for rows and secondary buttons, the quiet button, neutral tags, inline code, the festival band in charts.
- **Paper 3** (paper-3): quiet-button hover; the runway's target span.
- **Sheet** (sheet): input, select and search grounds; primary-button text.
- **Ink** (ink): headlines, values, the masthead and section rules, active tab text, the toast ground, pressed quiet buttons.
- **Ink 2** (ink-2): body copy in tables, ledes, on-track runway lines, the default chart data line and recent bars.
- **Muted** (muted): sub-lines, captions in sans, column heads, axis text, small-caps labels.
- **Faint** (faint): section-bar counts, the large section numerals, the dashed edges of target spans, neutral state rings.
- **Rule** (rule) and **Strong Rule** (rule-strong): hairlines between rows and figures; the strong step closes page heads, section bars, figure strips, table heads and the runway axis.
- **Chart Bar** (chart-bar): earlier-week bars in the product chart.

### Action
- **Moss** (moss): primary buttons, links and text links, focus outlines, input focus borders, the active tab underline. **Moss Deep** (moss-deep) is its hover and the ink for moss-washed text. **Moss Wash** (moss-wash) is the selection colour, the focus halo, approved tags and the margin note ground.

### Meaning
- **Brick** (brick, brick-wash): running short. Reorder runway lines and dates, the front-page run-out date, the worst forecast method, the demand-used-for-cover line, danger buttons, error toasts, flagged runway rows (a brick wash fading to paper), the pull-quote mark.
- **Ochre** (ochre for text, ochre-dot for marks, ochre-wash for tints): too much stock. Pause runway lines and dates, warning tags and state dots, rule conflicts in the drawer.

### Named Rules
**The One Action Colour Rule.** Moss is the only colour that fills or underlines something you can act on. No other hue appears on a button, link or focus state; brick appears on a control only for the reject action, and only as text and border on transparent.

**The Never Colour Alone Rule.** Brick and ochre never carry meaning by themselves. Every coloured line, dot or date sits beside words that say the same thing ("Reorder 240", "Pause, over the 4-week limit", "runs out 24 Oct"), and every runway row has an accessible label that states the run-out date and action.

**The Paper Ground Rule.** Every surface is the same oat paper with grain; sticky bars and the drawer repeat the grain rather than switching to a flat or frosted fill. Only inputs sit on the lighter Sheet.

## Typography

**Display and Reading Font:** Newsreader Variable (self-hosted, optical-size axis, roman and italic), falling back to Iowan Old Style and Georgia.
**Operating Font:** Instrument Sans Variable (self-hosted, weight axis), falling back to the system UI stack.
**Mono:** the system monospace stack, only for values inside formula lists.

**Character:** A newspaper's pairing. The serif is set at weight 400 throughout and gets its hierarchy from size and tight negative tracking; italic carries voice (the issue line, captions, margin notes, the pull-quote, the front-page emphasis). The sans is small and plain at 400 to 600.

### Hierarchy
- **Front headline** (serif 400, clamp 2.4 to 4.1rem, 1.02, -0.025em, balanced): the front page's one sentence; an italic brick phrase marks the date that matters.
- **Headline** (serif 400, clamp 1.9 to 2.9rem, 1.06, -0.022em, max 26ch, balanced): inner page heads.
- **Figure** (serif 400, 40px, 1.05, lining tabular): figure strips (32px under 640px); drawer figures 34px; docket counts 44px.
- **Section head** (serif 400, 30px, 1.1): numbered sections, beside a 52px faint numeral (34px under 900px).
- **Wordmark** (serif 500, 26px; 22px on phones) with "Planning Brief" in muted italic 400.
- **Section title** (serif 400, 22px): ruled section titles. **Subtitle** (serif 400, 20px): sub-heads in the drawer and pages; the drawer's product name sets it at 30px (26px on phones).
- **Lede** (serif 400, 17.5px, 1.55, ink-2, max 64ch): under every headline; 19px on the front page.
- **Margin note / caption** (serif italic 400, 16px, 1.5): chart captions, runway notes, empty states; the issue line is 15px italic.
- **Body** (sans 400, 14.5px, 1.6; paragraphs capped at 72ch).
- **Table** (sans 13.5px; product names 14.5px weight 500; sub-lines 12.5px muted).
- **Label** (sans 500, 12.5 to 13px): figure labels, field labels, legends, column heads (12px muted).
- **Small caps** (sans 600, 11.5px, 0.08em, uppercase, muted): group labels in the runway, the docket head, the metadata line above the drawer's product name.

### Named Rules
**The Headline States the Finding Rule.** A headline is a sentence with a verb and a number or date taken from the data ("Reorder three products. The first runs out on 24 October."), never a page name. The lede says why, and what happens next.

**The Read in Serif, Operate in Sans Rule.** Anything a person reads as prose or as a figure is Newsreader; anything they click, scan in a column or fill in is Instrument Sans. Figures inside running sans text keep the sans.

**The Lining Figures Rule.** Every figure that can sit above or beside another sets `font-variant-numeric: lining-nums tabular-nums` (the `.num` helper, numeric table cells, figure strips, drawer figures, runway dates, the issue line).

## Layout

One centred column, max 1200px, with 40px gutters (18px under 900px). The masthead sits in it; the section bar runs full width and sticks at the top; content follows in the same column with 72px bottom padding and closes with a colophon on an ink rule 64px below.

The front page is a two-column spread (1.65fr and at least 300px, 56px gap): headline, lede and byline on the left; the docket on the right behind a strong left rule. Numbered sections below use a 120px numeral column and a 32px gap; their content is indented 152px so it aligns under the section title. Within a section a "spread" pairs 1.5fr and 1fr with a 56px gap.

Inner pages open with a page head (headline, lede, up to two actions bottom-right) closed by a strong rule, 32px above the content. Content sits on a 12-column grid with 48px column gaps and 40px row gaps; spans of 3 to 12. A figure strip, when present, sits between the page head and the grid.

Responsive steps: under 1100px all spans go full width, the section indent drops, and the runway columns tighten to 170px and 180px; under 900px the spread, front page, pull-quote and section heads collapse to one column, the docket loses its rule, the runway keeps only the track, and the role picker moves from the section bar into the masthead; under 640px figure strips go two-up, forms go single column and charts switch to a narrow viewBox with larger type; under 600px stacking tables turn each row into a labelled two-column block.

### Named Rules
**The Rules Not Boxes Rule.** Structure is drawn with lines on paper: an ink rule over each section, hairlines between rows and figures, a strong rule to close a head or strip. There are no card backgrounds, borders around content blocks, rounded panels or page shadows.

## Elevation & Depth

Flat paper. Depth is a rule's weight, not a shadow: hairline (rule) separates, strong rule (rule-strong) closes, ink rule opens a section or the masthead (doubled under the masthead).

### Shadow Vocabulary
- **Drawer edge** (`box-shadow: -18px 0 40px -24px rgba(38, 33, 24, 0.35)`): the product drawer only, with a strong-rule left border, over a 22% ink scrim.
- **Focus halo** (`box-shadow: 0 0 0 3px var(--moss-wash)`): focused inputs, selects and search, with a moss border.

### Named Rules
**The One Floating Sheet Rule.** The drawer is the only surface that lifts off the page. Everything else, including sticky bars and the toast, is flat.

## Shapes

Nearly square. Controls (buttons, inputs, selects, icon buttons, toast) are 3px; tags and inline code 2px; state dots, figure dots and the dot-plot markers are round. Lines are 1px (2px for the active-tab and segmented underline, the runway line, the pull-quote aside rule and the margin note's left rule). Dashed lines mark only expectations: the edges of a target span and the demand-used-for-cover line. The front page's open quote mark is a 120px brick serif glyph.

## Components

### Masthead and section bar
- **Masthead:** serif wordmark left, italic issue line right ("No. {week} · {long date}", lining figures), then a double ink rule.
- **Section bar:** sticky, 46px, paper with grain, strong bottom rule. Sentence-case tabs at 13.5px in ink-2 with 26px gaps; the current tab is ink, weight 600, with a 2px moss underline. Pending counts follow the label in faint, tabular. The tab row scrolls horizontally with a 28px fade at its right edge.
- **Reading as:** a muted "Reading as" prefix with a borderless inline select ("Raghav, Planner"); right of the tabs on desktop, under the masthead under 900px.

### Page head
A small-caps kicker naming the section (Products, Exceptions, Approvals…; on the front page, "This week's call · stock as of …"), then a headline that states the finding, a serif lede, and at most one or two actions aligned to its baseline; a strong rule below. The kicker is part of the approved bulletin direction: it plays the role of a newspaper section slug, so it is always one or two plain words, never a slogan.

### Front page
- **Call:** front headline, lede with bolded quantities, a muted byline (rules version, product count, last sales week).
- **Docket ("On Raghav's desk"):** numbered list of three rows (Reorder, Pause, Needs judgment), each a 44px serif count beside a bold label and a plain sentence, on hairlines; then one full-width 46px moss button with the count of open lines and a serif arrow, and a fine line with who holds what.
- **Pull-quote:** brick quote mark, an italic serif sentence built from the sales rows, a sans citation, and an aside under a 2px ink rule saying why a person decides, ending in an "Open the evidence" text link.
- **Numbered sections:** faint serif numeral, 30px head, muted standfirst, indented content.
- **Forecast dot plot:** one row per method on a dotted hairline, a 12px ink-2 dot and a serif percentage; the worst method turns brick. "Further left is better" is written above it.
- **Margin note:** moss-wash ground, 2px moss left rule, a bold moss-deep lead-in and one sentence.
- **Colophon:** ink rule, an italic serif sentence on who decides, and a tabular line of rules version, run ID and "draft only, nothing leaves this app".

### Buttons
- **Shape:** 3px, 36px tall, 0 16px, sans 13.5px weight 500; small is 30px tall, 0 12px, 13px. Active nudges down 1px.
- **Primary:** moss with sheet text; hover moss-deep. A trailing arrow is set in the serif at 19px.
- **Secondary:** transparent with a strong-rule border; hover paper-2.
- **Quiet:** paper-2; hover paper-3; pressed (aria-pressed) inverts to ink with paper text.
- **Danger:** transparent, brick text, a pale brick border; hover or pressed fills brick-wash.
- **Disabled:** paper-2 ground, faint text, hairline border, not-allowed cursor.
- **Text link:** moss, 13.5px weight 600, underline on hover. Focus everywhere is a 2px moss outline offset 2px.

### Segmented filter
An underlined text row, not a pill track: 13.5px muted options 18px apart on a hairline; the pressed one is ink, weight 600, with a 2px ink underline.

### States and tags
- **State:** an 8px dot plus 13px ink-2 text. Moss dot for settled, ochre-dot for attention, brick dot and brick text for critical, ink for done or info; neutral and pending are hollow rings.
- **Tag:** 22px, 2px radius, 12px weight 500 on paper-2; crit, warn and ok use the matching wash with brick, ochre or moss-deep text; info is ink with paper text.

### Ruled section (Card)
No box. A 1px ink top rule, 12px above a 22px serif title with an optional 13.5px muted sub-line and a right slot; body follows 14px below; an optional foot sits on a hairline in 13px muted text.

### Figure strip (Kpi)
A row of figures between two strong rules, divided by hairlines. Each figure reads number first: the 40px serif value (with an optional 15px muted sans unit), then a 13px label (optionally led by an 8px dot), then a 12.5px note tinted brick when worsening, moss when good, ochre when attention is due. No count-up.

### The runway (signature)
Every product's run-out date on a 16-week calendar that starts at the stock date. A sticky axis under the section bar labels today (ink, bold, with an ink tick) and each month start. Rows are grouped under small-caps heads (Reorder, Raghav decides, Pause, On track, each with a count) and sorted by cover. Each row is one button: the product name (14.5px, weight 500, with "perishable" beneath), a track carrying month gridlines, the product's own target span (paper-3 with dashed faint edges), a 2px line from today to the run-out date ending in a 16px tick, and the date itself; products that last beyond the calendar end in a triangle with the date inside the track and an arrow. Line, tick and date are brick for reorder, ochre for pause, ink-2 otherwise. A margin note in italic serif closes the row ("**Reorder 240** if Raghav agrees", "**Pause** 5 months of stock"). Rows the rules cannot settle carry a brick wash fading to paper. A legend states every colour in words. Under 900px only the track column remains.

### Product drawer
Set like an article. Slides in from the right at min(680px, 100vw) on paper with grain, a strong left rule and the drawer-edge shadow. A sticky head on an ink rule carries the small-caps metadata line, the product name at 30px serif and a square close button. The body runs: a three-up figure row (cover, units a week, the action quantity) between hairlines, a sixteen-week chart with a legend, the decision controls with the current state, a "Why" section in prose, then disclosures (Formulas, Source rows, Data quality) with serif summaries and a serif "+" that turns to a cross. Escape and the scrim close it; page scroll locks while it is open.

### Charts
Data-drawn SVG on the paper, no animation. Gridlines are hairlines, axis text 12px muted sans (15px in the narrow viewBox). Data is ink-2 by default, earlier bars chart-bar, and only meaningful marks take brick or ochre. Festival weeks are a paper-2 band labelled "festival month" in italic serif on the chart itself. Values are written on the chart as serif callouts ("1,240 this week", "38.0 a week used for cover") so legends are needed only where a chart carries several encodings. On phones each chart switches to a narrow viewBox so type stays legible.

### Inputs
Sheet ground, strong-rule border, 3px radius, 14px text, 8px 10px padding; selects and search 36px tall. Field labels 12.5px weight 500 ink-2, 6px above. Focus turns the border moss with a 3px moss-wash halo.

### Tables
13.5px cells with 13px 12px padding on hairlines, the first column flush left; column heads 12px muted weight 500 on paper with grain above a strong rule, sticky under the section bar on tall tables; numeric columns right-aligned and tabular; clickable rows tint paper-2 on hover and open the drawer.

### Toast
Ink with paper text, 3px radius, bottom centre, rising 12px over 0.22s; errors switch it to brick.

### Motion
- **Scroll:** native. No smooth-scroll library.
- **Page:** content settles with a 0.24s opacity fade on `cubic-bezier(0.22, 1, 0.36, 1)`.
- **Drawer:** 0.26s transform slide on the same curve; scrim fades over 0.2s.
- **Controls:** 0.12s colour and border transitions; disclosure "+" rotates over 0.2s.
- **Data:** none. Charts and figures render in place.
- **Reduced motion:** every animation and transition collapses to 0.001ms.

### Named Rules
**The Dates Over Weeks Rule.** The runway shows when each product runs out as a calendar date, not weeks of cover. Weeks of cover appear only as a figure in the drawer, beside its target.

**The Nothing Loops Rule.** No motion repeats, follows the pointer or animates data. The page fades once and the drawer slides; that is all.

## Do's and Don'ts

### Do:
- **Do** write every headline as the finding, with a number or date from the data, followed by a serif lede.
- **Do** keep moss for actions only: primary buttons, links, focus, the active tab.
- **Do** pair every brick or ochre mark with words that say the same thing.
- **Do** draw structure with rules on paper: ink to open, hairline to separate, strong rule to close.
- **Do** set reading in Newsreader and operating in Instrument Sans, with lining tabular figures on every number.
- **Do** label charts in place and shade festival weeks with a named band.
- **Do** make every product row open the drawer with its evidence.
- **Do** honour reduced motion and keep content visible without script.

### Don't:
- **Don't** bring back the dashboard: no sidebar, white cards, card shadows, rounded panels or KPI tiles.
- **Don't** use cool greys, pure black or pure white; the palette is oat and ink.
- **Don't** fill a button or link with brick or ochre, or use moss to tell data categories apart.
- **Don't** let colour be the only signal of short or over stock.
- **Don't** express the runway as weeks of cover or as a bar chart.
- **Don't** add count-ups, draw-ons, scroll-triggered reveals, smooth scrolling or anything that loops.
- **Don't** title a page with its name when the data supports a sentence.
