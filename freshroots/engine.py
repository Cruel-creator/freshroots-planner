"""Recommendation engine: metrics -> documented rules -> priority layer -> explanation.

`evaluate_sku` is pure (primitive inputs) so every rule and conflict path can be
unit-tested; `analyse` wires it to the validated CSV data.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from . import rules as R
from .calendar_utils import festival_lookup, is_festival_month, shift_week, week_label, week_month
from .config import RULE_VERSION, Config
from .exceptions import detect_exceptions
from .ingest import ValidationResult

ACTION_REORDER_NOW = "Reorder now"
ACTION_REORDER_HIGH = "Reorder (high demand)"
ACTION_PAUSE = "Pause next order"
ACTION_NONE = "No action"
ACTION_REVIEW = "Planner decision required"
REORDER_ACTIONS = {ACTION_REORDER_NOW, ACTION_REORDER_HIGH}
ALL_ACTIONS = [ACTION_REORDER_NOW, ACTION_REORDER_HIGH, ACTION_PAUSE, ACTION_NONE, ACTION_REVIEW]

# Prototype rule-priority layer (ASSUMPTION, not Freshroots policy). The first
# matching step decides the single recommended action; every triggered flag is kept.
PRIORITY_STEPS = [
    ("1. Data blocker", "Cover or perishability cannot be determined -> planner decides; no quantity."),
    ("2. Demand vs stock conflict", "High demand together with any overstock flag -> planner decides; no quantity."),
    ("3. Perishable safety", "Perishable SKUs use the 3-4 week window. An order that would push cover above 4 weeks -> planner decides."),
    ("4. Stockout risk", "Below 6 weeks -> reorder now (1.5x standard quantity if also high demand)."),
    ("5. High demand", "More than 20% above baseline with cover 6-14 weeks -> reorder 1.5x standard quantity."),
    ("6. Overstock risk", "Above 14 weeks -> pause next order."),
    ("7. No action", "All checks within thresholds."),
]


def _fmt(x: float | None, digits: int = 1) -> str:
    if x is None:
        return "n/a"
    if isinstance(x, float) and math.isinf(x):
        return "infinite"
    return f"{x:,.{digits}f}"


def evaluate_sku(
    *,
    sku_id: str,
    window_labels: list[str],
    weekly_units: dict[str, float],
    stock: float | None,
    is_perishable: bool | None,
    standard_qty: float | None,
    festival: bool | None,
    festival_weeks_in_baseline: int = 0,
    cfg: Config,
) -> dict:
    """Apply rules A-E and the priority layer to one SKU.

    window_labels: the `baseline_weeks` most recent complete weeks, oldest first.
    weekly_units: week label -> units for weeks present in the data (missing weeks stay missing).
    """
    review: list[str] = []
    conflicts: list[str] = []
    reasons: list[str] = []
    flags: list[str] = []

    base_labels = window_labels[-cfg.baseline_weeks:]
    recent_labels = window_labels[-cfg.recent_weeks:]
    base_vals = [weekly_units[w] for w in base_labels if w in weekly_units]
    recent_vals = [weekly_units[w] for w in recent_labels if w in weekly_units]
    missing_base = [w for w in base_labels if w not in weekly_units]

    recent_avg = R.average(recent_vals) if len(recent_vals) == cfg.recent_weeks else None
    baseline_avg = R.average(base_vals) if len(base_vals) == cfg.baseline_weeks else None
    if missing_base:
        review.append(f"{len(missing_base)} of {cfg.baseline_weeks} baseline weeks have no sales row "
                      f"({', '.join(missing_base[:4])}{'...' if len(missing_base) > 4 else ''})")
    # Fallback for cover only: average of available weeks when at least 4 exist (flagged).
    demand_basis = baseline_avg
    demand_basis_note = f"{cfg.baseline_weeks}-week average"
    if baseline_avg is None and len(base_vals) >= cfg.recent_weeks:
        demand_basis = R.average(base_vals)
        demand_basis_note = f"average of {len(base_vals)} available weeks (incomplete history)"

    change = R.demand_change(recent_avg, baseline_avg)
    high = R.is_high_demand(recent_avg, baseline_avg, cfg.high_demand_threshold)
    if high:
        flags.append(R.HIGH_DEMAND)
        reasons.append(f"Last {cfg.recent_weeks} weeks average {_fmt(recent_avg)} units/week, "
                       f"{change:+.1%} vs the {cfg.baseline_weeks}-week average of {_fmt(baseline_avg)} "
                       f"(rule: more than {cfg.high_demand_threshold:.0%}).")
    elif high is None:
        review.append("High-demand rule not evaluable (needs complete 4- and 12-week windows with non-zero baseline)")

    adjusted = None
    uplift_applied = False
    if demand_basis is not None:
        adjusted, uplift_applied = R.festival_adjust(demand_basis, festival, cfg.festival_uplift)
        if uplift_applied:
            flags.append(R.FESTIVAL_UPLIFT)
            reasons.append(f"Festival month: {demand_basis_note} {_fmt(demand_basis)} x {1 + cfg.festival_uplift:.2f} "
                           f"= {_fmt(adjusted)} units/week used for cover checks.")
            if festival_weeks_in_baseline:
                reasons.append(f"Note: {festival_weeks_in_baseline} of the {cfg.baseline_weeks} baseline weeks already fall "
                               f"in festival months; the uplift is applied once to the full average as Rule A states.")
    if festival is None:
        review.append("Festival status unknown: planning month missing from calendar.csv (no uplift applied)")

    cover = R.weeks_of_cover(stock, adjusted)
    if stock is None:
        review.append("No usable inventory record")
    elif adjusted is None:
        review.append("Not enough sales history to estimate weekly demand")
    elif adjusted == 0:
        review.append("Zero demand in the baseline window")

    perishable_window = bool(is_perishable) and cfg.perishable_replaces_standard_windows
    if is_perishable is None:
        review.append("Perishability unknown")
    if cover is not None:
        if is_perishable:
            pf = R.perishable_cover_flag(cover, cfg.perishable_min_weeks, cfg.perishable_max_weeks)
            flags.append(pf)
            reasons.append(f"Perishable SKU: {_fmt(cover)} weeks of cover vs target window "
                           f"{cfg.perishable_min_weeks:g}-{cfg.perishable_max_weeks:g} weeks.")
        if not perishable_window:
            sf = R.standard_cover_flags(cover, cfg.stockout_weeks, cfg.overstock_weeks)
            flags.extend(sf)
            if R.STOCKOUT_RISK in sf:
                reasons.append(f"{_fmt(cover)} weeks of cover is below the {cfg.stockout_weeks:g}-week minimum.")
            if R.OVERSTOCK_RISK in sf:
                reasons.append(f"{_fmt(cover)} weeks of cover exceeds the {cfg.overstock_weeks:g}-week maximum.")

    has_overstock = R.OVERSTOCK_RISK in flags or R.PERISHABLE_OVERSTOCK_RISK in flags
    multiplier = cfg.high_demand_multiplier if high else 1.0
    rule_qty = standard_qty * multiplier if standard_qty else None
    max_cover = cfg.perishable_max_weeks if perishable_window else cfg.overstock_weeks
    min_cover = cfg.perishable_min_weeks if perishable_window else cfg.stockout_weeks

    def projected(q: float | None) -> float | None:
        if q is None or stock is None or not adjusted:
            return None
        return (stock + q) / adjusted

    action, qty, step = ACTION_NONE, 0.0, "7. No action"
    if cover is None or is_perishable is None:
        action, qty, step = ACTION_REVIEW, None, "1. Data blocker"
    elif high and has_overstock:
        conflicts.append("High-demand signal conflicts with an overstock flag: reorder at 1.5x vs pause next order.")
        action, qty, step = ACTION_REVIEW, None, "2. Demand vs stock conflict"
    elif perishable_window and (R.PERISHABLE_REPLENISH_RISK in flags or high):
        proj = projected(rule_qty)
        if rule_qty is not None and proj is not None and R.gt(proj, cfg.perishable_max_weeks):
            conflicts.append(f"Ordering {rule_qty:,.0f} units ({'1.5x ' if high else ''}standard quantity) would give "
                             f"{_fmt(proj)} weeks of cover, above the {cfg.perishable_max_weeks:g}-week perishable maximum.")
            action, qty, step = ACTION_REVIEW, None, "3. Perishable safety"
        else:
            action = ACTION_REORDER_NOW if R.PERISHABLE_REPLENISH_RISK in flags else ACTION_REORDER_HIGH
            qty, step = rule_qty, "3. Perishable safety"
    elif perishable_window and R.PERISHABLE_OVERSTOCK_RISK in flags:
        action, qty, step = ACTION_PAUSE, 0.0, "3. Perishable safety"
    elif R.STOCKOUT_RISK in flags:
        action, qty, step = ACTION_REORDER_NOW, rule_qty, "4. Stockout risk"
    elif high:
        action, qty, step = ACTION_REORDER_HIGH, rule_qty, "5. High demand"
    elif R.OVERSTOCK_RISK in flags:
        action, qty, step = ACTION_PAUSE, 0.0, "6. Overstock risk"

    if action in REORDER_ACTIONS:
        if standard_qty is None:
            qty = None
            review.append("Standard reorder quantity unknown: planner must enter a quantity")
        else:
            proj = projected(qty)
            if proj is not None and R.gt(proj, max_cover) and not perishable_window:
                conflicts.append(f"Ordering {qty:,.0f} units would give {_fmt(proj)} weeks of cover, "
                                 f"above the {max_cover:g}-week maximum.")

    qty_to_max = None
    shortfall = excess = None
    if stock is not None and adjusted:
        qty_to_max = max(0.0, math.floor(max_cover * adjusted - stock))
        shortfall = max(0.0, min_cover * adjusted - stock)
        excess = max(0.0, stock - max_cover * adjusted)

    if conflicts:
        review.append("Conflicting signals")
    needs_review = bool(review) or action == ACTION_REVIEW

    qty_basis = {
        ACTION_REORDER_NOW: f"standard qty {standard_qty:,.0f}" + (f" x {cfg.high_demand_multiplier:g} (high demand)" if high else "")
        if standard_qty else "standard qty unknown",
        ACTION_REORDER_HIGH: f"standard qty {standard_qty:,.0f} x {cfg.high_demand_multiplier:g} (Rule B)"
        if standard_qty else "standard qty unknown",
        ACTION_PAUSE: "pause: no order",
        ACTION_NONE: "no order",
        ACTION_REVIEW: "planner to decide",
    }[action]

    explanation = _explain(sku_id, action, qty, cover, adjusted, stock, reasons, conflicts, review, step,
                           qty_to_max if action == ACTION_REVIEW else None)

    return {
        "sku_id": sku_id,
        "recent_4w_units": sum(recent_vals) if len(recent_vals) == cfg.recent_weeks else None,
        "recent_4w_avg": recent_avg,
        "baseline_12w_avg": baseline_avg,
        "demand_change_pct": change,
        "demand_basis": demand_basis,
        "demand_basis_note": demand_basis_note,
        "festival_month": festival,
        "festival_uplift_applied": uplift_applied,
        "festival_weeks_in_baseline": festival_weeks_in_baseline,
        "adjusted_weekly_demand": adjusted,
        "current_stock": stock,
        "weeks_of_cover": cover,
        "flags": flags,
        "flag_reasons": reasons,
        "conflicts": conflicts,
        "action": action,
        "priority_step": step,
        "standard_qty": standard_qty,
        "recommended_qty": qty,
        "qty_basis": qty_basis,
        "projected_cover_after_order": projected(qty) if qty else None,
        "max_qty_within_window": qty_to_max,
        "shortfall_to_min_cover_units": shortfall,
        "excess_over_max_cover_units": excess,
        "needs_review": needs_review,
        "review_reasons": review,
        "data_quality_status": "Complete" if not review else "Review: " + "; ".join(review),
        "explanation": explanation,
        "source_weeks": base_labels,
        "rule_version": RULE_VERSION,
    }


def _explain(sku, action, qty, cover, demand, stock, reasons, conflicts, review, step, qty_to_max) -> str:
    parts = []
    if stock is not None and demand is not None:
        parts.append(f"{sku} has {stock:,.0f} units on hand against {_fmt(demand)} units/week of adjusted demand "
                     f"({_fmt(cover)} weeks of cover).")
    parts.extend(reasons)
    parts.extend(conflicts)
    if action == ACTION_REVIEW:
        parts.append("The rules do not give a single safe answer, so no quantity is proposed.")
        if qty_to_max is not None:
            parts.append(f"For reference, at most {qty_to_max:,.0f} units keeps cover within the maximum window.")
    elif action in REORDER_ACTIONS:
        parts.append(f"Recommendation: {action.lower()}" + (f", {qty:,.0f} units." if qty else ", quantity needs planner input."))
    elif action == ACTION_PAUSE:
        parts.append("Recommendation: pause the next order.")
    else:
        parts.append("All rule checks are within thresholds: no order needed.")
    if review:
        parts.append("Needs planner review: " + "; ".join(review) + ".")
    parts.append(f"Priority step applied: {step}.")
    return " ".join(parts)


@dataclass
class Analysis:
    recommendations: pd.DataFrame
    exceptions: pd.DataFrame
    weekly: pd.DataFrame            # SKU x week with month and festival flag
    analysis_date: object
    anchor_week: str | None
    window_labels: list[str]
    planning_month: str | None
    planning_month_festival: bool | None


def _window(anchor: tuple[int, int], n: int) -> list[str]:
    return [week_label(*shift_week(anchor[0], anchor[1], -i)) for i in range(n - 1, -1, -1)]


def analyse(v: ValidationResult, cfg: Config) -> Analysis:
    sales = v.usable("weekly_sales")
    skus = v.usable("sku_master")
    inv = v.usable("current_inventory")
    cal = v.usable("calendar")
    dists = v.usable("distributor_master")

    lookup = festival_lookup(cal) if not cal.empty else {}
    analysis_date = inv["as_of"].max().date() if not inv.empty else None
    planning_month = f"{analysis_date.year:04d}-{analysis_date.month:02d}" if analysis_date else None
    planning_festival = is_festival_month(planning_month, lookup) if planning_month else None

    weekly = pd.DataFrame(columns=["SKU_ID", "week", "week_start", "units", "month", "is_festival"])
    anchor = None
    window: list[str] = []
    if not sales.empty:
        weekly = sales[["SKU_ID", "week", "iso_year", "iso_week", "week_start", "units"]].copy()
        weekly["month"] = [week_month(int(y), int(w)) for y, w in zip(weekly["iso_year"], weekly["iso_week"])]
        weekly["is_festival"] = weekly["month"].map(lambda m: lookup.get(m))
        last = max(zip(weekly["iso_year"].astype(int), weekly["iso_week"].astype(int)),
                   key=lambda t: t[0] * 100 + t[1])
        anchor = week_label(*last)
        window = _window(last, cfg.baseline_weeks)

    stock_by_sku = inv.groupby("SKU_ID")["units_on_hand"].sum().to_dict() if not inv.empty else {}
    loc_by_sku = inv.groupby("SKU_ID")["Location"].agg(lambda s: ", ".join(sorted(set(s)))).to_dict() if not inv.empty else {}
    dist_names = dict(zip(dists["Distributor_ID"], dists["Distributor_Name"])) if not dists.empty else {}
    month_of = dict(zip(weekly["week"], weekly["month"])) if not weekly.empty else {}

    recs = []
    for _, s in skus.iterrows():
        sku = s["SKU_ID"]
        units = weekly[weekly["SKU_ID"] == sku].set_index("week")["units"].to_dict() if not weekly.empty else {}
        fest_weeks = sum(1 for w in window if lookup.get(month_of.get(w, "")) is True)
        std = s["standard_qty"]
        r = evaluate_sku(
            sku_id=sku,
            window_labels=window,
            weekly_units=units,
            stock=stock_by_sku.get(sku),
            is_perishable=s["is_perishable"],
            standard_qty=None if pd.isna(std) else float(std),
            festival=planning_festival,
            festival_weeks_in_baseline=fest_weeks,
            cfg=cfg,
        )
        dist_id = str(s["Distributor_ID"]).strip()
        r.update({
            "sku_name": s["SKU_Name"],
            "category": s["Category"],
            "perishability": s["Perishability"],
            "is_perishable": s["is_perishable"],
            "unit": s["Unit_of_Measure"],
            "mapped_distributor_id": dist_id,
            "mapped_distributor": f"{dist_id} {dist_names.get(dist_id, '(not in master)')}",
            "scope": f"SKU-level demand (all distributors); stock at {loc_by_sku.get(sku, 'no location on record')}",
            "inventory_as_of": str(analysis_date) if analysis_date else None,
            "weeks_of_history": len(units),
            "planning_month": planning_month,
        })
        recs.append(r)

    rec_df = pd.DataFrame(recs)
    exc_df = detect_exceptions(rec_df, weekly, window, cfg)
    if not rec_df.empty and not exc_df.empty:
        exc_skus = set(exc_df["sku_id"])
        rec_df["exception_codes"] = rec_df["sku_id"].map(
            lambda k: sorted(exc_df.loc[exc_df["sku_id"] == k, "code"].unique().tolist()))
        rec_df["needs_review"] = rec_df["needs_review"] | rec_df["sku_id"].isin(exc_skus)
    elif not rec_df.empty:
        rec_df["exception_codes"] = [[] for _ in range(len(rec_df))]
    return Analysis(rec_df, exc_df, weekly, analysis_date, anchor, window, planning_month, planning_festival)
