import math

from conftest import LABELS, flat, run_sku

from freshroots import rules as R
from freshroots.engine import ACTION_PAUSE, ACTION_REORDER_HIGH, ACTION_REORDER_NOW, ACTION_REVIEW, ACTION_NONE


def step_series(first8, last4):
    return {w: float(first8 if i < 8 else last4) for i, w in enumerate(LABELS)}


# ---- 4-week vs 12-week demand ------------------------------------------------
def test_four_vs_twelve_week_averages(cfg):
    r = run_sku(cfg, units=step_series(90, 120))
    assert r["recent_4w_avg"] == 120
    assert r["baseline_12w_avg"] == 100          # (8*90 + 4*120) / 12; the 12 weeks include the last 4
    assert math.isclose(r["demand_change_pct"], 0.20)
    assert r["recent_4w_units"] == 480


def test_high_demand_exactly_20_percent_is_not_flagged(cfg):
    r = run_sku(cfg, units=step_series(90, 120))
    assert R.HIGH_DEMAND not in r["flags"]


def test_high_demand_above_20_percent_is_flagged_with_1_5x_quantity(cfg):
    r = run_sku(cfg, units=step_series(90, 121), stock=1000.0)   # cover ~9.9 weeks: no stock flag
    assert R.HIGH_DEMAND in r["flags"]
    assert r["action"] == ACTION_REORDER_HIGH
    assert r["recommended_qty"] == 150.0


def test_is_high_demand_helper_boundaries():
    assert R.is_high_demand(120, 100) is False
    assert R.is_high_demand(120.0001, 100) is True
    assert R.is_high_demand(50, 0) is None


# ---- festival uplift ---------------------------------------------------------
def test_festival_uplift_applied_once(cfg):
    r = run_sku(cfg, festival=True, stock=1000.0)
    assert r["adjusted_weekly_demand"] == 125.0
    assert r["demand_basis"] == 100.0
    assert r["flags"].count(R.FESTIVAL_UPLIFT) == 1
    assert math.isclose(r["weeks_of_cover"], 8.0)


def test_no_uplift_outside_festival_months(cfg):
    r = run_sku(cfg, festival=False)
    assert r["adjusted_weekly_demand"] == 100.0
    assert not r["festival_uplift_applied"]


def test_festival_uplift_is_applied_before_threshold_checks(cfg):
    # 700 units / 100 = 7 weeks (fine) but / 125 = 5.6 weeks (stockout risk)
    assert R.STOCKOUT_RISK not in run_sku(cfg, stock=700.0, festival=False)["flags"]
    assert R.STOCKOUT_RISK in run_sku(cfg, stock=700.0, festival=True)["flags"]


def test_unknown_festival_status_flags_review(cfg):
    r = run_sku(cfg, festival=None)
    assert not r["festival_uplift_applied"]
    assert r["needs_review"]


# ---- stockout / overstock ----------------------------------------------------
def test_stockout_below_six_weeks(cfg):
    r = run_sku(cfg, stock=599.0)
    assert R.STOCKOUT_RISK in r["flags"]
    assert r["action"] == ACTION_REORDER_NOW
    assert r["recommended_qty"] == 100.0


def test_exactly_six_weeks_is_not_stockout(cfg):
    r = run_sku(cfg, stock=600.0)
    assert R.STOCKOUT_RISK not in r["flags"]
    assert r["action"] == ACTION_NONE


def test_overstock_above_fourteen_weeks(cfg):
    r = run_sku(cfg, stock=1401.0)
    assert R.OVERSTOCK_RISK in r["flags"]
    assert r["action"] == ACTION_PAUSE
    assert r["recommended_qty"] == 0.0


def test_exactly_fourteen_weeks_is_not_overstock(cfg):
    assert R.OVERSTOCK_RISK not in run_sku(cfg, stock=1400.0)["flags"]


def test_stockout_with_high_demand_orders_1_5x(cfg):
    r = run_sku(cfg, units=step_series(90, 130), stock=200.0)
    assert {R.HIGH_DEMAND, R.STOCKOUT_RISK} <= set(r["flags"])
    assert r["action"] == ACTION_REORDER_NOW
    assert r["recommended_qty"] == 150.0


# ---- perishables -------------------------------------------------------------
def test_perishable_below_three_weeks(cfg):
    r = run_sku(cfg, perishable=True, stock=299.0, std=50.0)
    assert R.PERISHABLE_REPLENISH_RISK in r["flags"]
    assert r["action"] == ACTION_REORDER_NOW


def test_perishable_exactly_three_and_four_weeks_within_target(cfg):
    for stock in (300.0, 400.0):
        r = run_sku(cfg, perishable=True, stock=stock)
        assert R.PERISHABLE_WITHIN_TARGET in r["flags"], stock
        assert r["action"] == ACTION_NONE


def test_perishable_above_four_weeks(cfg):
    r = run_sku(cfg, perishable=True, stock=401.0)
    assert R.PERISHABLE_OVERSTOCK_RISK in r["flags"]
    assert r["action"] == ACTION_PAUSE


def test_perishable_windows_replace_standard_windows(cfg):
    r = run_sku(cfg, perishable=True, stock=450.0)   # 4.5 weeks: overstock for perishables, stockout for standard
    assert R.STOCKOUT_RISK not in r["flags"]
    assert R.PERISHABLE_OVERSTOCK_RISK in r["flags"]


def test_perishable_order_that_breaches_max_window_goes_to_planner(cfg):
    r = run_sku(cfg, perishable=True, stock=250.0, std=500.0)   # (250+500)/100 = 7.5 weeks > 4
    assert r["action"] == ACTION_REVIEW
    assert r["recommended_qty"] is None
    assert r["conflicts"]
    assert r["max_qty_within_window"] == 150.0


# ---- zero / missing ----------------------------------------------------------
def test_zero_demand_with_stock_is_overstock_and_review(cfg):
    r = run_sku(cfg, units=flat(0), stock=50.0)
    assert math.isinf(r["weeks_of_cover"])
    assert R.OVERSTOCK_RISK in r["flags"]
    assert r["needs_review"]


def test_zero_demand_and_zero_stock_is_undefined(cfg):
    r = run_sku(cfg, units=flat(0), stock=0.0)
    assert r["weeks_of_cover"] is None
    assert r["action"] == ACTION_REVIEW


def test_zero_stock_with_demand_is_stockout(cfg):
    r = run_sku(cfg, stock=0.0)
    assert r["weeks_of_cover"] == 0.0
    assert R.STOCKOUT_RISK in r["flags"]


def test_missing_inventory_blocks_quantity(cfg):
    r = run_sku(cfg, stock=None)
    assert r["action"] == ACTION_REVIEW
    assert r["recommended_qty"] is None
    assert any("inventory" in x.lower() for x in r["review_reasons"])


def test_missing_weeks_are_not_treated_as_zero(cfg):
    units = flat(100)
    del units[LABELS[3]]
    r = run_sku(cfg, units=units)
    assert r["baseline_12w_avg"] is None            # full 12-week baseline not available
    assert r["demand_basis"] == 100.0               # fallback over 11 available weeks, flagged
    assert r["needs_review"]


def test_insufficient_history_cannot_evaluate(cfg):
    r = run_sku(cfg, units=flat(100, n=3))
    assert r["action"] == ACTION_REVIEW
    assert r["needs_review"]


def test_unknown_perishability_goes_to_review(cfg):
    r = run_sku(cfg, perishable=None)
    assert r["action"] == ACTION_REVIEW


# ---- conflicts and unknown standard quantity ----------------------------------
def test_high_demand_and_overstock_conflict_keeps_both_flags(cfg):
    r = run_sku(cfg, units=step_series(90, 130), stock=5000.0)
    assert R.HIGH_DEMAND in r["flags"] and R.OVERSTOCK_RISK in r["flags"]
    assert r["action"] == ACTION_REVIEW
    assert r["recommended_qty"] is None
    assert r["priority_step"].startswith("2.")
    assert r["needs_review"]


def test_unknown_standard_quantity_requires_planner_input(cfg):
    r = run_sku(cfg, stock=100.0, std=None)
    assert r["action"] == ACTION_REORDER_NOW
    assert r["recommended_qty"] is None
    assert r["needs_review"]
    assert "unknown" in r["qty_basis"]


def test_every_recommendation_has_an_explanation(cfg):
    for stock in (0.0, 300.0, 700.0, 2000.0):
        assert run_sku(cfg, stock=stock)["explanation"]
