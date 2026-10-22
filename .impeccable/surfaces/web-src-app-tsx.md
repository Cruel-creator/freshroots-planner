---
version: 1
slug: "web-src-app-tsx"
primary_target: "web/src/App.tsx"
related_targets: ["web/src"]
---

## Scope

Whole web app (web/), Operate mode. Audience: Raghav (planner), procurement, Priya (analyst), Deepa, and the MESA class watching a demo. Job: see what needs a decision, decide it with traceable evidence, export a draft PO. Constraints: the Python engine is the source of truth; no claims beyond the data; projections labelled.

## Direction contract

THESIS: A calm operations dashboard where every number is one click from its evidence. It refuses the marketing-page look of the previous build (full-bleed black bands, 88px headlines) and equally the grey admin template; density and clarity come first, with Apple-grade motion as the finish.

OWN-WORLD: Light canvas #f5f6f8, white cards with 1px #e5e7eb borders and 12px radius, ink #111827, secondary #6b7280. Freshroots green #15803d as the single action and brand colour; state colours red #dc2626, amber #d97706, green #16a34a only for meaning; data series slate/teal/amber. Inter Variable with tabular numerals. Fixed 240px white sidebar with icon nav; 60px sticky header with page title, role selector and one primary action.

STORY: The planner opens the overview, reads the KPI row (reorders, units, pauses, waiting decisions, exceptions, forecast error), scans the charts, opens a SKU from the decision queue, decides, and moves to the workbench.

FIRST VIEWPORT: Sidebar left. Header with "Overview" and the analysis date. A welcome strip over a faint interactive dot grid (React Bits DotGrid) with the date and festival-month note, then six KPI cards in one row, then the weekly sales chart (2/3 width) beside the recommendation mix donut.

FORM: Standard dashboard shell with a 12-column card grid. Signature move: the weeks-of-cover chart card, every SKU on one axis against its target band, bars growing as it scrolls into view. Motion: Lenis inertial scroll on the GSAP ticker, staggered card entrances, CountUp numerals, line draw-on. seed: none (unavailable). Direction pinned by the user.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
