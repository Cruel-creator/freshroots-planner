"""Raghav's documented forecasting rules as pure functions.

Boundaries follow the case wording exactly: "more than 20%", "below 6 weeks",
"exceeds 14 weeks", "minimum 3 / maximum 4 weeks". A value exactly on a
threshold does not trigger the flag. Comparisons tolerate float noise so that
e.g. 120/100 - 1 is treated as exactly 20%.
"""
from __future__ import annotations

import math

HIGH_DEMAND = "HIGH_DEMAND"
STOCKOUT_RISK = "STOCKOUT_RISK"
OVERSTOCK_RISK = "OVERSTOCK_RISK"
PERISHABLE_REPLENISH_RISK = "PERISHABLE_REPLENISH_RISK"
PERISHABLE_OVERSTOCK_RISK = "PERISHABLE_OVERSTOCK_RISK"
PERISHABLE_WITHIN_TARGET = "PERISHABLE_WITHIN_TARGET"
FESTIVAL_UPLIFT = "FESTIVAL_UPLIFT_APPLIED"

RISK_FLAGS = {HIGH_DEMAND, STOCKOUT_RISK, OVERSTOCK_RISK, PERISHABLE_REPLENISH_RISK, PERISHABLE_OVERSTOCK_RISK}

FLAG_LABELS = {
    HIGH_DEMAND: "High demand",
    STOCKOUT_RISK: "Stockout risk",
    OVERSTOCK_RISK: "Overstock risk",
    PERISHABLE_REPLENISH_RISK: "Perishable: below 3 wks",
    PERISHABLE_OVERSTOCK_RISK: "Perishable: above 4 wks",
    PERISHABLE_WITHIN_TARGET: "Perishable: within 3-4 wks",
    FESTIVAL_UPLIFT: "Festival uplift applied",
}

_TOL = 1e-9


def gt(a: float, b: float) -> bool:
    return a > b and not math.isclose(a, b, rel_tol=0.0, abs_tol=_TOL)


def lt(a: float, b: float) -> bool:
    return a < b and not math.isclose(a, b, rel_tol=0.0, abs_tol=_TOL)


def average(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def demand_change(recent_avg: float | None, baseline_avg: float | None) -> float | None:
    """(4-week average / 12-week average) - 1. None when the baseline is zero or missing."""
    if recent_avg is None or baseline_avg is None or baseline_avg <= 0:
        return None
    return recent_avg / baseline_avg - 1.0


def is_high_demand(recent_avg: float | None, baseline_avg: float | None, threshold: float = 0.20) -> bool | None:
    """Rule B. True when the 4-week average is MORE than `threshold` above the 12-week average."""
    change = demand_change(recent_avg, baseline_avg)
    if change is None:
        return None
    return gt(change, threshold)


def festival_adjust(base_weekly_demand: float, festival: bool | None, uplift: float = 0.25) -> tuple[float, bool]:
    """Rule A. Applies the uplift once; returns (adjusted demand, applied?)."""
    if festival:
        return base_weekly_demand * (1.0 + uplift), True
    return base_weekly_demand, False


def weeks_of_cover(stock: float | None, weekly_demand: float | None) -> float | None:
    """Usable stock / adjusted weekly demand.

    None = cannot be calculated (missing stock or demand, or 0 stock with 0 demand).
    inf  = stock on hand with zero demand.
    """
    if stock is None or weekly_demand is None:
        return None
    if weekly_demand > 0:
        return stock / weekly_demand
    return math.inf if stock > 0 else None


def standard_cover_flags(cover: float, stockout_weeks: float = 6.0, overstock_weeks: float = 14.0) -> list[str]:
    """Rules C and D for non-perishable SKUs."""
    if lt(cover, stockout_weeks):
        return [STOCKOUT_RISK]
    if gt(cover, overstock_weeks):
        return [OVERSTOCK_RISK]
    return []


def perishable_cover_flag(cover: float, min_weeks: float = 3.0, max_weeks: float = 4.0) -> str:
    """Rule E for perishable SKUs."""
    if lt(cover, min_weeks):
        return PERISHABLE_REPLENISH_RISK
    if gt(cover, max_weeks):
        return PERISHABLE_OVERSTOCK_RISK
    return PERISHABLE_WITHIN_TARGET
