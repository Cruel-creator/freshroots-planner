# Freshroots Demand Planning prototype

MESA AI-Native Track, Term 2 case: *Deepa's 90-Day Mandate*.

This prototype builds **Option A (Demand Planning)** and **Option C (Operations Intelligence)** on the supplied data:

- **Option A**: Raghav's documented rules run automatically on the SAP-style exports. Every SKU gets an explained recommendation, which then goes through planner sign-off and procurement approval.
- **Option C**: weekly sales signals go to Priya to triage. Procurement must acknowledge an open signal before any purchase-order line for that SKU can be approved, so an order is never placed on data that is already stale.

Nothing is sent to SAP, Zoho or any other system. The only output is CSV files.

## Run it

You need Python 3.11 or later (tested on 3.14.7, Windows 11).

```bash
python -m venv C:\venvs\freshroots
```

```bash
C:\venvs\freshroots\Scripts\python.exe -m pip install -r requirements-dev.txt
```

```bash
cd web && npm ci && npm run build
```

```bash
C:\venvs\freshroots\Scripts\python.exe serve.py
```

Open http://localhost:8000. This serves the web UI (React, built into `web/dist` by the step above) and its JSON API. If you're on macOS or Linux, use `python -m venv .venv` and `.venv/bin/python` instead.

The web UI is **The Planning Brief**, set like a weekly bulletin rather than a dashboard:
- **Front page:** a masthead and a headline that states the week's call ("Reorder five products. The first runs out on 31 October.").
- **Evidence:** the exception that needs a person, as a pull-quote.
- **The runway:** a calendar of the date each product runs out, against where it should run out.
- **Inner pages:** each opens with a headline that states its finding, then ruled sections instead of cards.

Type is Newsreader (editorial serif) with Instrument Sans. One colour acts (moss); brick means running short and ochre means overstocked, always with words. Motion is minimal: native scrolling, a short fade when a page settles, and the drawer sliding in. It switches off under `prefers-reduced-motion`.

To change the UI, rebuild it with Node 20 or later:

```bash
cd web && npm install && npm run build
```

For live editing, run `serve.py` and `npm run dev` in `web/` together, then open http://localhost:5173 (Vite proxies `/api` to port 8000).

The original Streamlit version still works as a fallback:

```bash
C:\venvs\freshroots\Scripts\python.exe -m streamlit run app.py
```

> **Windows path-length note.** Put the virtual environment at a short path, as above. If it sits under a deeply nested folder, pyarrow's DLL path goes over Windows' 260-character limit and every table fails with `ImportError: DLL load failed ... filename or extension is too long`.

Other commands:

```bash
C:\venvs\freshroots\Scripts\python.exe -m pytest -q
```

```bash
C:\venvs\freshroots\Scripts\python.exe scripts\generate_reports.py
```

### Configuration (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `FRESHROOTS_DATA_DIR` | `data/raw` | Folder that holds the five CSVs |
| `DATABASE_URL` | unset | Postgres (Neon) connection string. When set, runs, approvals and the audit log live there instead of SQLite |
| `FRESHROOTS_DB_PATH` | `data/freshroots.db` | SQLite database used when `DATABASE_URL` is not set |
| `FRESHROOTS_PERISHABLE_REPLACES_STANDARD` | `true` | Perishable 3–4-week windows replace the 6/14-week windows |
| `GEMINI_API_KEY` | unset | Google AI Studio key. Turns on short Gemini notes on the Exceptions page; they never change a number or a status |
| `GEMINI_MODEL` | `gemini-flash-latest` | Gemini model for those notes |
| `FRESHROOTS_LLM_PROVIDER` | `gemini` if a key is set, else `disabled` | Set to `disabled` to turn the notes off while keeping the key |
| `FRESHROOTS_PORT` | `8000` | Port for `serve.py` |

Without `DATABASE_URL`, delete `data/freshroots.db` to reset all approvals.

## Deploy (Vercel + Neon)

- `vercel.json` builds the web UI (`web/dist`) as static files and runs the API as one Python function, `api/index.py`. Every `/api/*` request goes to that function. The region is Singapore (`sin1`), next to the Neon database.
- Set `DATABASE_URL` (and optionally `GEMINI_API_KEY`) in the Vercel project's environment variables. The tables are created on first start.
- Every push to `main` redeploys. To change the data, commit new CSVs to `data/raw/`.
- `.vercelignore` keeps the local-only parts (Streamlit, scripts, tests, reports) out of the deployment.
- The prototype has **no sign-in**: anyone with the URL can approve lines as any role. Turn on Vercel Deployment Protection, or add SSO, before sharing it beyond the team.

## Screens

| Page (web UI) | What it does |
|---|---|
| The brief | The week's call as a front page, Raghav's desk (reorder / pause / needs judgment), the exception as a pull-quote, the runway of run-out dates, demand, and whether the forecast can be trusted |
| Products | Searchable, sortable product table with filters; selecting a row opens the product drawer (chart, explanation, formulas, source rows, decision controls) |
| Exceptions | Raghav's queue: the signal, its source data, the rules triggered, why automation isn't enough, the next action, an optional Gemini note, and approve / override / reject |
| Approvals | Pipeline counts, planner and procurement approvals, human checkpoints for each line, run selector, recommendations CSV, draft PO export, audit log |
| Sales alerts | Option C: weekly pulse, which of the 12 report metrics the data covers, alert triage (Priya), acknowledgement (procurement), alert history |
| Forecast | Leakage-free chronological backtest at 1–4 weeks ahead: WAPE and MAE against an explicit baseline, by week and by product |
| Data | File status, findings with CSV line numbers, what the data cannot show, data dictionary, file fingerprints |
| Plan | ROI scenarios, the 90-day plan, open business questions |

The Streamlit fallback has the same content in its own screens.

Use **Acting as** in the sub-navigation bar (or the Streamlit sidebar) to switch between Raghav (planner), Procurement, Priya (analyst) and Deepa (viewer). There's no authentication in the prototype; the chosen identity is written to the audit log.

## Workflow and controls

`Generated → Pending planner review → Planner approved / Planner overridden → Pending procurement approval → Procurement approved → Exported as draft` (or `Rejected`)

- Raghav signs off every line. A line with no single rule answer (a conflict or a data blocker) cannot be approved as-is; it needs an override with an action, a quantity and a reason.
- A reorder with a missing quantity cannot be approved.
- Overrides and rejections need a reason of at least 10 characters.
- Only procurement can approve PO lines and export the draft PO. The draft file says "DRAFT - NOT SUBMITTED" on every line.
- An open Option C signal for a SKU blocks procurement approval until Priya triages it and procurement acknowledges it.
- `ExternalOrderGateway` always raises an error, and a test checks that the package imports no network libraries.
- Each run stores the rule version, the rule parameters and a SHA-256 hash of every input file, so it can be reproduced.

## Deliverables in `reports/`

- `validation_report.md`, `validation_findings.csv`, `data_dictionary.csv`
- `rules_and_assumptions.md`: rule definitions, prototype assumptions, open questions
- `backtest_report.md`, `backtest_predictions.csv`
- `recommendations_example.csv`: the recommendation export built from the real input data
- `operations_signals_history.csv`

## What the data says (verified)

- **Validation:** all five files load with 0 errors and 2 warnings. The warnings are two mapped distributors in Karnataka and Gujarat, outside the case's Maharashtra and Goa scope.
- **Scale:** the sample has 15 SKUs × 16 weeks (2026-W27 to W42), against 400 SKUs and 3 years in the case.
- **Granularity:** sales are SKU-level only, with no distributor split.
- **Recommendations:** for an analysis date of 2026-10-19 (a festival month):
  - 5 reorders: 3 stockout-risk SKUs (SKU001 at 750 units, because it is also high demand; SKU003; SKU013) and 2 perishable replenishments (SKU004, SKU011);
  - 2 pauses (SKU006 overstock, SKU007 perishable above 4 weeks);
  - 8 no action.
- **Backtest (60 one-week-ahead forecasts):** the festival-uplifted estimate has **16.0% WAPE vs 8.7%** for the plain 12-week average. October sales did not rise 25% for most SKUs. The uplift needs revisiting with Raghav before any pilot.
- **Option C:** no SKU crossed a signal threshold in the latest week (W42), so no PO line is held. The history scan does detect past movements, for example SKU001's +38% spike in W39.

## Known limitations

- No lead times, open POs, in-transit stock, expiry dates, prices or suppliers. Cover uses on-hand stock only, and impact is shown in units, not rupees.
- Business outcomes (stockouts, write-offs) can't be backtested without historical stock snapshots; only a pilot can measure them.
- Signals are weekly because the data is weekly. The real fix for the ₹9L incident needs daily SAP extracts.
- The rule precedence, the perishable-window replacement and the signal thresholds are prototype assumptions.
- There's no authentication and no real SAP or Zoho integration.

## Next steps for production

1. Confirm the open business definitions with Raghav and procurement (see `rules_and_assumptions.md`).
2. Get the full SAP export (400 SKUs, 3 years, distributor-level), plus lead times and open POs, and rerun the backtest.
3. Revisit or recalibrate the festival uplift for each category.
4. Add authentication (SSO) and a scheduled twice-weekly run (daily for signals).
5. Build a Zoho Inventory draft-PO import, with authorised credentials and human submission.
6. Run the 2-week parallel pilot against a control group and evaluate the results.
