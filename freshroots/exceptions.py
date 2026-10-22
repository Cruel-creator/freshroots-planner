"""Exception layer: deterministic statistical checks that route SKUs to Raghav.

This layer never changes a rule result or a quantity. It only adds exception
records and marks the recommendation for planner review.
"""
from __future__ import annotations

import statistics

import pandas as pd

from .config import Config

ASSIGNEE = "Raghav Kulkarni (Senior Demand Planner)"

EXCEPTION_COLUMNS = ["sku_id", "code", "category", "signal", "source_data", "rules_triggered",
                     "why_not_automated", "suggested_action", "assigned_to", "ai_note", "ai_review_category"]


def modified_z(x: float, reference: list[float]) -> float | None:
    """Iglewicz-Hoaglin modified z-score of x against reference (median/MAD). None if MAD is 0."""
    if len(reference) < 4:
        return None
    med = statistics.median(reference)
    mad = statistics.median([abs(v - med) for v in reference])
    if mad == 0:
        return None
    return 0.6745 * (x - med) / mad


def _row(sku, code, category, signal, source, rules, why, action) -> dict:
    return {"sku_id": sku, "code": code, "category": category, "signal": signal, "source_data": source,
            "rules_triggered": rules, "why_not_automated": why, "suggested_action": action,
            "assigned_to": ASSIGNEE, "ai_note": None, "ai_review_category": None}


def detect_exceptions(recs: pd.DataFrame, weekly: pd.DataFrame, window: list[str], cfg: Config) -> pd.DataFrame:
    out: list[dict] = []
    if recs.empty:
        return pd.DataFrame(columns=EXCEPTION_COLUMNS)
    for _, r in recs.iterrows():
        sku = r["sku_id"]
        flags = ", ".join(r["flags"]) or "none"
        series = weekly[weekly["SKU_ID"] == sku].sort_values("week_start") if not weekly.empty else weekly
        hist = series["units"].tolist() if not series.empty else []
        labels = series["week"].tolist() if not series.empty else []

        if r["weeks_of_history"] < cfg.baseline_weeks:
            out.append(_row(sku, "INSUFFICIENT_HISTORY", "New product / short history",
                            f"{r['weeks_of_history']} weeks of sales history (rules need {cfg.baseline_weeks})",
                            f"weekly_sales.csv: {', '.join(labels) or 'no rows'}", flags,
                            "The 12-week baseline does not exist, so the documented rules cannot be applied as written.",
                            "Planner sets demand from launch plan or comparable SKUs."))

        if len(hist) >= 5:
            latest, ref = hist[-1], hist[-(cfg.baseline_weeks + 1):-1]
            z = modified_z(latest, ref)
            if z is not None and abs(z) > cfg.anomaly_modified_z:
                direction = "above" if z > 0 else "below"
                ref_labels = labels[-(cfg.baseline_weeks + 1):-1]
                out.append(_row(sku, "UNUSUAL_LATEST_WEEK", "Demand anomaly",
                                f"Latest week {labels[-1]} = {latest:,.0f} units, {direction} the prior "
                                f"{len(ref)}-week pattern (modified z = {z:+.1f}, threshold {cfg.anomaly_modified_z})",
                                f"weekly_sales.csv: {labels[-1]} vs {ref_labels[0]}..{ref_labels[-1]} "
                                f"(median {statistics.median(ref):,.0f})", flags,
                                "A statistical outlier may be a scheme, a one-off bulk order or a data error; "
                                "the rules cannot tell which.",
                                "Check with sales/distributors whether the change is temporary before acting on it."))

        change = r["demand_change_pct"]
        if change is not None and change < -cfg.demand_drop_threshold and abs(change + cfg.demand_drop_threshold) > 1e-9:
            out.append(_row(sku, "DEMAND_DROP", "Demand anomaly",
                            f"Last 4 weeks are {change:.1%} vs the 12-week average",
                            f"weekly_sales.csv: {window[-4]}..{window[-1]} vs {window[0]}..{window[-1]}", flags,
                            "No documented rule covers falling demand (e.g. competitor schemes, as in the case).",
                            "Confirm the cause; consider reducing or pausing the next order."))

        if r["conflicts"]:
            out.append(_row(sku, "RULE_CONFLICT", "Rule conflict", " | ".join(r["conflicts"]),
                            f"weeks_of_cover={r['weeks_of_cover']}, demand_change={change}", flags,
                            "The documented rules give contradictory actions and their precedence is not defined in the case.",
                            "Planner chooses the action and quantity and records the reason."))

        data_reasons = [x for x in r["review_reasons"] if x != "Conflicting signals"]
        if data_reasons:
            out.append(_row(sku, "DATA_GAP", "Missing or inconsistent data", "; ".join(data_reasons),
                            "See Data Quality page for the source rows", flags,
                            "A required input is missing, so a calculated recommendation would be unreliable.",
                            "Fix the source data or enter the missing value as a planner override."))

    return pd.DataFrame(out, columns=EXCEPTION_COLUMNS)
