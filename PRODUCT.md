# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

React (Vite, TypeScript) frontend over the existing Python engine through a small JSON API (FastAPI), chosen by the user over restyling Streamlit. The Streamlit app stays as a fallback. Libraries the user asked for: Lenis, GSAP, Vanta, React Bits.

## Users

- Raghav Kulkarni, Senior Demand Planner at Freshroots: reviews twice-weekly reorder recommendations for every SKU and decides the exceptions.
- Procurement: approves every purchase-order line and exports a draft PO.
- Priya Sharma, data analyst: triages operations signals (Option C).
- Deepa Nair, Head of Operations, and the CEO: read the overview.
- Mihirr Sose and the MESA cohort: see the prototype presented in class. The user wants the presentation and the daily tool served equally.

## Product Purpose

Turn Raghav's documented forecasting rules into explained recommendations that are refreshed twice a week instead of monthly, with humans approving every decision. Success means lower stockout and overstock losses (reported at ₹28–34L a quarter). Option C adds weekly sales signals that procurement must acknowledge before ordering.

## Positioning

Every number traces back to a source row and a documented rule. Nothing is automated past a human: no purchase order leaves the app, conflicts get no automatic quantity, and every override needs a reason.

## Operating Context

MESA AI-Native Track, Term 2 case "Deepa's 90-Day Mandate". The data is a 15-SKU, 16-week sample (2026-W27 to W42), inventory as of 2026-10-19, and a festival calendar (Oct, Nov, Mar). Freshroots is a regional FMCG brand in Maharashtra and Goa with SAP and Zoho Inventory.

## Capabilities and Constraints

Validation with line-level findings; rules A–E; a rule-priority layer; an exception layer; planner and procurement approvals with an audit log in SQLite; a draft PO CSV; a leakage-free backtest; Option C signal triage. There's no SAP or Zoho integration and no authentication. Lead times, prices, suppliers and expiry dates are not in the data.

## Brand Commitments

The user pinned the look, then clarified it: the product must look like a clean data dashboard (sidebar navigation, KPI cards, chart grid, tables, like the team's earlier dashboards), not like a marketing website. "Apple" applies only to the feel of scrolling and animation (smooth inertial scroll, eased entrances, numbers counting, charts drawing on). The landing page gets a subtle background that suits a data product. Freshroots has no supplied logo or brand assets.

## Evidence on Hand

The five CSVs in data/raw, the case PDF in docs/, and the reports in reports/. Do not invent savings, customers or benchmarks. Projections must be labelled as projections.

## Product Principles

- Every figure is traceable to a row and a rule.
- A human decides wherever money or judgment is at stake.
- Say what the data cannot show.
- Make the decision that's needed today the first thing a planner sees.
