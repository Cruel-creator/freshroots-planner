import math

import pandas as pd
import pytest

from freshroots.backtest import forecast_at_origin, run_backtest, wape
from freshroots.config import Config
from freshroots.engine import ACTION_PAUSE, ACTION_REORDER_NOW, analyse
from freshroots.exports import recommendations_frame
from freshroots.ingest import validate
from freshroots.llm import DisabledExplainer, attach_ai_notes
from freshroots.ops_intel import scan_signals

REAL = Config()

GOOD = {
    "weekly_sales.csv": "SKU_ID,Week,Units_Sold\n" + "".join(f"S1,2026-W{w:02d},100\n" for w in range(27, 43)),
    "sku_master.csv": "SKU_ID,SKU_Name,Category,Perishability,Standard_Reorder_Qty,Unit_of_Measure,Distributor_ID\n"
                      "S1,Thing,Snack,Low,100,Units,D1\n",
    "distributor_master.csv": "Distributor_ID,Distributor_Name,Region,Status\nD1,Dist,Maharashtra,Active\n",
    "current_inventory.csv": "SKU_ID,Location,Units_On_Hand,As_Of_Date\nS1,Pune,500,2026-10-19\n",
    "calendar.csv": "Year,Month,Year_Month,Is_Festival_Month\n2026,9,2026-09,FALSE\n2026,10,2026-10,TRUE\n",
}


def write(tmp_path, overrides=None):
    files = {**GOOD, **(overrides or {})}
    for name, body in files.items():
        if body is not None:
            (tmp_path / name).write_text(body, encoding="utf-8")
    return tmp_path


def checks(v):
    return set(v.issues["check"])


# ---- real data --------------------------------------------------------------
def test_real_files_validate_without_errors():
    v = validate(REAL.data_dir)
    assert v.error_count == 0
    s = v.summaries
    assert s["weekly_sales"]["rows"] == 240 and s["weekly_sales"]["unique_skus"] == 15 and s["weekly_sales"]["weeks"] == 16
    assert s["sku_master"]["rows"] == 15 and s["current_inventory"]["rows"] == 15
    assert s["calendar"]["festival_months"] == ["2025-03", "2025-10", "2025-11", "2026-03", "2026-10", "2026-11"]
    assert "case_inconsistency" in checks(v)        # Karnataka / Gujarat distributors


def test_real_data_recommendations():
    a = analyse(validate(REAL.data_dir), REAL)
    r = a.recommendations.set_index("sku_id")
    assert len(r) == 15 and a.anchor_week == "2026-W42" and a.planning_month_festival is True
    sku1 = r.loc["SKU001"]
    assert math.isclose(sku1["demand_change_pct"], 261 / (2579 / 12) - 1)
    assert sku1["action"] == ACTION_REORDER_NOW and sku1["recommended_qty"] == 750
    assert r.loc["SKU006", "action"] == ACTION_PAUSE
    out = recommendations_frame(a.recommendations)
    assert {"SKU_ID", "Recommended_Action", "Reason", "Weeks_Of_Cover"} <= set(out.columns)


# ---- invalid data -----------------------------------------------------------
def test_invalid_rows_are_reported_not_silently_dropped(tmp_path):
    bad_sales = (GOOD["weekly_sales.csv"]
                 + "S1,2026-W99,10\n"          # invalid week
                 + "S1,2026-W30,-5\n"          # negative, and a conflicting duplicate key
                 + "S9,2026-W30,10\n"          # unknown SKU
                 + "S1,2026-W31,abc\n")        # non-numeric
    v = validate(write(tmp_path, {"weekly_sales.csv": bad_sales}))
    found = checks(v)
    assert {"invalid_week", "negative_value", "unmatched_reference", "invalid_number"} <= found
    assert v.issues.loc[v.issues["check"] == "invalid_week", "line"].iloc[0] == 18
    assert v.frames["weekly_sales"]["excluded"].sum() >= 4


def test_conflicting_duplicates_excluded(tmp_path):
    v = validate(write(tmp_path, {"weekly_sales.csv": GOOD["weekly_sales.csv"] + "S1,2026-W30,250\n"}))
    assert "duplicate_key" in checks(v)
    ws = v.usable("weekly_sales")
    assert "2026-W30" not in set(ws["week"])


def test_missing_inventory_and_bad_master_fields(tmp_path):
    v = validate(write(tmp_path, {
        "current_inventory.csv": "SKU_ID,Location,Units_On_Hand,As_Of_Date\nS1,Pune,-3,2026-10-19\n",
        "sku_master.csv": "SKU_ID,SKU_Name,Category,Perishability,Standard_Reorder_Qty,Unit_of_Measure,Distributor_ID\n"
                          "S1,Thing,Snack,Maybe,,Units,D1\n",
    }))
    assert {"negative_value", "missing_inventory", "invalid_category"} <= checks(v)
    rec = analyse(v, REAL).recommendations.iloc[0]
    assert rec["needs_review"] and rec["recommended_qty"] is None


def test_missing_file_reported(tmp_path):
    v = validate(write(tmp_path, {"calendar.csv": None}))
    assert "missing_file" in checks(v)


def test_missing_required_column(tmp_path):
    v = validate(write(tmp_path, {"weekly_sales.csv": "SKU_ID,Week\nS1,2026-W30\n"}))
    assert "required_column" in checks(v)


# ---- backtest ---------------------------------------------------------------
def test_backtest_has_no_future_leakage():
    series = pd.Series([100.0] * 12 + [100.0, 500.0, 900.0])
    before = forecast_at_origin(series, 11, REAL, target_is_festival=False)
    series.iloc[12:] = [0.0, 0.0, 0.0]
    after = forecast_at_origin(series, 11, REAL, target_is_festival=False)
    assert before == after == {"baseline_12w": 100.0, "rules_engine": 100.0, "recent_4w": 100.0}


def test_backtest_needs_twelve_weeks():
    assert forecast_at_origin(pd.Series([1.0] * 11), 10, REAL, False) is None


def test_backtest_on_real_data_is_chronological():
    a = analyse(validate(REAL.data_dir), REAL)
    bt = run_backtest(a.weekly, REAL, horizon=1)
    assert set(bt.summary["observations"]) == {60}
    assert (bt.predictions["origin"] < bt.predictions["target"]).all()
    assert set(bt.predictions["target"]) == {"2026-W39", "2026-W40", "2026-W41", "2026-W42"}
    assert len(bt.excluded) == 15 * 11


def test_wape_handles_zero_actuals():
    assert wape(pd.Series([0.0, 0.0]), pd.Series([1.0, 2.0])) is None
    assert wape(pd.Series([100.0]), pd.Series([90.0])) == pytest.approx(0.1)


# ---- operations signals and LLM guard ---------------------------------------
def weekly_frame(values):
    weeks = [f"2026-W{w:02d}" for w in range(30, 30 + len(values))]
    return pd.DataFrame({"SKU_ID": "S1", "week": weeks,
                         "week_start": pd.date_range("2026-07-20", periods=len(values), freq="7D"),
                         "units": [float(v) for v in values]})


def test_signal_drop_threshold_is_strict():
    assert scan_signals(weekly_frame([100, 100, 100, 100, 85])).empty          # exactly -15%
    s = scan_signals(weekly_frame([100, 100, 100, 100, 84]))
    assert list(s["signal_type"]) == ["DROP_VS_TREND"] and bool(s["is_latest_week"].iloc[0])


def test_signal_spike_and_week_on_week_drop():
    s = scan_signals(weekly_frame([100, 100, 100, 100, 130, 105]))
    assert "SPIKE_VS_TREND" in set(s["signal_type"]) and "DROP_WEEK_ON_WEEK" in set(s["signal_type"])


def test_real_latest_week_has_no_signals_but_history_does():
    a = analyse(validate(REAL.data_dir), REAL)
    s = scan_signals(a.weekly)
    assert not s["is_latest_week"].any()
    assert ((s["sku_id"] == "SKU001") & (s["week"] == "2026-W39") & (s["signal_type"] == "SPIKE_VS_TREND")).any()


def test_disabled_llm_changes_nothing():
    exc = pd.DataFrame([{"sku_id": "S1", "code": "X", "signal": "s", "source_data": "d", "rules_triggered": "r",
                         "ai_note": None, "ai_review_category": None}])
    assert attach_ai_notes(exc, DisabledExplainer()).equals(exc)


def test_ai_notes_only_touch_note_columns():
    class Fake:
        enabled, name = True, "fake"

        def explain(self, facts):
            if facts["sku_id"] == "S2":
                raise TimeoutError("provider down")
            return "Check the scheme calendar.", "Not a category"

    exc = pd.DataFrame([{"sku_id": s, "code": "X", "signal": "s", "source_data": "d", "rules_triggered": "r",
                         "recommended_qty": 100, "ai_note": None, "ai_review_category": None} for s in ("S1", "S2")])
    out = attach_ai_notes(exc, Fake())
    assert out.loc[0, "ai_note"] == "Check the scheme calendar." and out.loc[0, "ai_review_category"] == "Unclear"
    assert out.loc[1, "ai_note"] is None
    assert out.drop(columns=["ai_note", "ai_review_category"]).equals(exc.drop(columns=["ai_note", "ai_review_category"]))
