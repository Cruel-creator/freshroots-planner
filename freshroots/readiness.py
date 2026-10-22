"""Plan content: ROI scenarios, the 90-day plan and the open business questions."""
from __future__ import annotations

import pandas as pd


def roi_scenarios(budget_lakh: float = 15.0, loss_low: float = 28.0, loss_high: float = 34.0,
                  reductions: tuple[float, ...] = (0.10, 0.20, 0.30)) -> pd.DataFrame:
    """Scenario table. Reductions are assumptions; the budget is treated as full one-time cost (assumption)."""
    rows = []
    for r in reductions:
        lo, hi = loss_low * r, loss_high * r
        rows.append({
            "Assumed loss reduction": f"{r:.0%}",
            "Quarterly saving (Rs lakh)": f"{lo:.1f} - {hi:.1f}",
            "Annual saving (Rs lakh)": f"{lo * 4:.1f} - {hi * 4:.1f}",
            "Quarters to recover Rs 15L": f"{budget_lakh / hi:.1f} - {budget_lakh / lo:.1f}",
        })
    return pd.DataFrame(rows)


PLAN = [
    (1, 15, "Discover and validate", "Inspect data; validate source files; confirm missing business definitions "
     "(standard quantity, rule precedence, lead times); agree baselines."),
    (16, 30, "Build the core", "Ingestion pipeline; documented business rules; first recommendation outputs."),
    (31, 45, "Workflow and UI", "Dashboard; exception handling; planner and procurement approvals."),
    (46, 60, "Backtest", "Historical backtests; data-quality fixes; resolve rule conflicts with Raghav."),
    (61, 75, "Parallel pilot", "Run alongside the manual process; capture overrides and feedback."),
    (76, 90, "Evaluate and decide", "Evaluate pilot results; fix critical issues; documentation; rollout recommendation."),
]


def plan_frame() -> pd.DataFrame:
    return pd.DataFrame([{"Start day": s, "End day": e, "Phase": p, "Work": w} for s, e, p, w in PLAN])


OPEN_QUESTIONS = [
    "Does Rule B's 1.5x replace the standard order or add to it? (Prototype: the order quantity is 1.5x standard.)",
    "Which rule wins when high demand and overstock both trigger? (Prototype: planner decides, no quantity.)",
    "Do perishable windows replace the 6/14-week windows? (Prototype: yes, configurable.)",
    "Festival uplift: should it apply when the baseline window already contains festival weeks? (Prototype: applied once, noted.)",
    "What does Distributor_ID in the SKU master mean, given 1,200 distributors per the case?",
    "Lead times, open purchase orders, in-transit stock and shelf life are not in the data.",
    "Two mapped distributors are in Karnataka and Gujarat, outside the case's Maharashtra and Goa scope.",
]
