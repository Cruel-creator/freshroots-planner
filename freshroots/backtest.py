"""Leakage-free chronological backtest of the demand estimate used by the rules.

At each forecast origin t only weeks <= t are visible. Methods:
  * baseline_12w  - 12-week moving average (the explicitly defined baseline)
  * rules_engine  - 12-week moving average x (1 + uplift) when the target week's
                    month is a festival month (Rule A, as the engine applies it)
  * recent_4w     - 4-week moving average (reference)
Business outcomes (stockouts, write-offs) are NOT evaluated: there is no
historical inventory or price data to build ground truth from.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import Config

METHODS = {
    "baseline_12w": "12-week moving average (baseline)",
    "rules_engine": "12-week average + festival uplift (rules engine)",
    "recent_4w": "4-week moving average (reference)",
}


@dataclass
class BacktestResult:
    predictions: pd.DataFrame      # one row per SKU x origin x target
    summary: pd.DataFrame          # per method: n, MAE, WAPE
    by_week: pd.DataFrame          # per target week x method
    excluded: pd.DataFrame         # skipped origins and why
    notes: list[str]


def forecast_at_origin(series: pd.Series, origin_pos: int, cfg: Config, target_is_festival: bool | None) -> dict | None:
    """series: units indexed 0..n-1 in chronological order. Uses only positions <= origin_pos."""
    hist = series.iloc[: origin_pos + 1]
    if len(hist) < cfg.baseline_weeks:
        return None
    base = hist.iloc[-cfg.baseline_weeks:].mean()
    recent = hist.iloc[-cfg.recent_weeks:].mean()
    uplift = (1 + cfg.festival_uplift) if target_is_festival else 1.0
    return {"baseline_12w": base, "rules_engine": base * uplift, "recent_4w": recent}


def wape(actual: pd.Series, forecast: pd.Series) -> float | None:
    denom = actual.abs().sum()
    if denom == 0:
        return None
    return float((actual - forecast).abs().sum() / denom)


def run_backtest(weekly: pd.DataFrame, cfg: Config, horizon: int = 1) -> BacktestResult:
    rows, excluded = [], []
    notes = [
        "Chronological, expanding origin: each forecast uses only weeks up to its origin.",
        f"Horizon: {horizon} week(s) ahead. Origins need {cfg.baseline_weeks} prior weeks.",
        "Festival status of the target week comes from calendar.csv (week assigned to the month of its Thursday).",
        "Stockout/overstock outcomes are not simulated: no historical inventory snapshots, lead times or prices exist in the data.",
    ]
    if weekly.empty:
        return BacktestResult(pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), notes)

    for sku, grp in weekly.sort_values("week_start").groupby("SKU_ID"):
        grp = grp.reset_index(drop=True)
        expected = pd.date_range(grp["week_start"].iloc[0], grp["week_start"].iloc[-1], freq="7D")
        if len(expected) != len(grp):
            excluded.append({"sku_id": sku, "origin": None, "reason": "gaps in weekly series; SKU excluded"})
            continue
        for pos in range(len(grp) - horizon):
            target = pos + horizon
            if pos + 1 < cfg.baseline_weeks:
                excluded.append({"sku_id": sku, "origin": grp.at[pos, "week"],
                                 "reason": f"fewer than {cfg.baseline_weeks} weeks of history"})
                continue
            fc = forecast_at_origin(grp["units"], pos, cfg, grp.at[target, "is_festival"])
            for method, value in fc.items():
                rows.append({"sku_id": sku, "origin": grp.at[pos, "week"], "target": grp.at[target, "week"],
                             "target_month": grp.at[target, "month"], "target_festival": bool(grp.at[target, "is_festival"]),
                             "method": method, "forecast": value, "actual": grp.at[target, "units"]})

    pred = pd.DataFrame(rows)
    exc = pd.DataFrame(excluded, columns=["sku_id", "origin", "reason"])
    if pred.empty:
        return BacktestResult(pred, pd.DataFrame(), pd.DataFrame(), exc, notes)
    pred["abs_error"] = (pred["actual"] - pred["forecast"]).abs()

    def agg(g: pd.DataFrame) -> pd.Series:
        return pd.Series({"observations": len(g), "MAE": g["abs_error"].mean(), "WAPE": wape(g["actual"], g["forecast"])})

    summary = pred.groupby("method").apply(agg, include_groups=False).reset_index()
    summary["description"] = summary["method"].map(METHODS)
    by_week = pred.groupby(["target", "target_festival", "method"]).apply(agg, include_groups=False).reset_index()
    return BacktestResult(pred, summary, by_week, exc, notes)
