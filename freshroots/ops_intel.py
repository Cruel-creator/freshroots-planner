"""Option C - Operations Intelligence.

The case's problem is not who sees the data but how fast someone acts when a
metric moves. This module:
  * computes the weekly operations pulse from the metrics the data supports,
  * scans every week for sales signals (deterministic thresholds),
  * routes signals from the latest week to Priya (analyst) to triage and to
    procurement to acknowledge before any PO line for that SKU is approved.
"""
from __future__ import annotations

import pandas as pd

from . import rules as R
from .engine import Analysis

SIGNAL_NEW = "New"
SIGNAL_SURFACED = "Surfaced to procurement"
SIGNAL_DISMISSED = "Dismissed by analyst"
SIGNAL_ACKNOWLEDGED = "Acknowledged by procurement"
SIGNAL_OPEN = {SIGNAL_NEW, SIGNAL_SURFACED}
SIGNAL_STATUSES = [SIGNAL_NEW, SIGNAL_SURFACED, SIGNAL_DISMISSED, SIGNAL_ACKNOWLEDGED]

# Proposed thresholds (prototype assumptions, to be agreed with Priya and procurement).
DROP_VS_PRIOR4 = 0.15
DROP_WOW = 0.15
SPIKE_VS_PRIOR4 = 0.25

SIGNAL_COLUMNS = ["signal_id", "sku_id", "week", "signal_type", "latest_units", "reference_units",
                  "change_pct", "severity", "message", "is_latest_week"]

# The case names five of the twelve weekly metrics; the rest are not specified.
METRIC_CATALOG = [
    ("Sales volume", "Available", "Sum of units sold in the latest complete week (weekly_sales.csv)."),
    ("Stockout incidents", "Proxy", "SKUs below minimum cover today. True stockout events need daily stock history."),
    ("Overstock value", "Proxy (units)", "Units above maximum cover. Value in rupees needs prices, which are not in the data."),
    ("Order fulfilment rate", "Not available", "Needs order lines and shipped quantities from SAP."),
    ("Distributor complaints", "Not available", "Needs a complaints log; distributor service has no structured data."),
    ("Remaining 7 metrics", "Not specified", "The case says 'a handful of others' without naming them."),
]


def scan_signals(weekly: pd.DataFrame, drop_prior4: float = DROP_VS_PRIOR4, drop_wow: float = DROP_WOW,
                 spike_prior4: float = SPIKE_VS_PRIOR4) -> pd.DataFrame:
    """Check every week (with 4 prior weeks) of every SKU against the thresholds. Uses only past weeks."""
    rows = []
    if weekly.empty:
        return pd.DataFrame(columns=SIGNAL_COLUMNS)
    latest_week = weekly.sort_values("week_start")["week"].iloc[-1]
    for sku, g in weekly.sort_values("week_start").groupby("SKU_ID"):
        units, weeks = g["units"].tolist(), g["week"].tolist()
        for i in range(4, len(units)):
            x, prev, prior4 = units[i], units[i - 1], sum(units[i - 4:i]) / 4
            checks = []
            if prior4 > 0:
                ch = x / prior4 - 1
                if R.lt(ch, -drop_prior4):
                    checks.append(("DROP_VS_TREND", prior4, ch, "high",
                                   f"{x:,.0f} units vs {prior4:,.0f} average of the previous 4 weeks ({ch:+.1%})"))
                elif R.gt(ch, spike_prior4):
                    checks.append(("SPIKE_VS_TREND", prior4, ch, "medium",
                                   f"{x:,.0f} units vs {prior4:,.0f} average of the previous 4 weeks ({ch:+.1%})"))
            if prev > 0:
                ch = x / prev - 1
                if R.lt(ch, -drop_wow) and not any(c[0] == "DROP_VS_TREND" for c in checks):
                    checks.append(("DROP_WEEK_ON_WEEK", prev, ch, "medium",
                                   f"{x:,.0f} units vs {prev:,.0f} the week before ({ch:+.1%})"))
            for typ, ref, ch, sev, msg in checks:
                rows.append({"signal_id": f"{sku}:{weeks[i]}:{typ}", "sku_id": sku, "week": weeks[i],
                             "signal_type": typ, "latest_units": x, "reference_units": ref, "change_pct": ch,
                             "severity": sev, "message": msg, "is_latest_week": weeks[i] == latest_week})
    return pd.DataFrame(rows, columns=SIGNAL_COLUMNS)


def weekly_pulse(a: Analysis) -> pd.DataFrame:
    """Metrics the data supports, latest complete week vs the week before."""
    w = a.weekly
    if w.empty:
        return pd.DataFrame()
    tot = w.groupby(["week", "week_start"], as_index=False)["units"].sum().sort_values("week_start")
    latest, prev = tot.iloc[-1], tot.iloc[-2] if len(tot) > 1 else None
    r = a.recommendations
    below_min = int(r["flags"].map(lambda f: R.STOCKOUT_RISK in f or R.PERISHABLE_REPLENISH_RISK in f).sum())
    above_max = int(r["flags"].map(lambda f: R.OVERSTOCK_RISK in f or R.PERISHABLE_OVERSTOCK_RISK in f).sum())
    excess = pd.to_numeric(r["excess_over_max_cover_units"], errors="coerce").sum()
    rows = [
        {"Metric": "Sales volume (units)", "Latest": f"{latest['units']:,.0f} ({latest['week']})",
         "Previous": f"{prev['units']:,.0f} ({prev['week']})" if prev is not None else "n/a",
         "Change": f"{latest['units'] / prev['units'] - 1:+.1%}" if prev is not None and prev["units"] else "n/a",
         "Basis": "weekly_sales.csv"},
        {"Metric": "SKUs below minimum cover (stockout proxy)", "Latest": str(below_min), "Previous": "n/a",
         "Change": "n/a", "Basis": "current_inventory.csv snapshot; no stock history"},
        {"Metric": "SKUs above maximum cover", "Latest": str(above_max), "Previous": "n/a", "Change": "n/a",
         "Basis": "current_inventory.csv snapshot"},
        {"Metric": "Units above maximum cover (overstock proxy)", "Latest": f"{excess:,.0f}", "Previous": "n/a",
         "Change": "n/a", "Basis": "No prices: units, not rupees"},
    ]
    return pd.DataFrame(rows)
