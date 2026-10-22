"""Write the static deliverables in reports/ from the real input files.

Usage: python scripts/generate_reports.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from freshroots.backtest import METHODS, run_backtest  # noqa: E402
from freshroots.config import RULE_VERSION, load_config  # noqa: E402
from freshroots.engine import PRIORITY_STEPS, analyse  # noqa: E402
from freshroots.exports import recommendations_frame  # noqa: E402
from freshroots.ingest import data_dictionary, validate  # noqa: E402
from freshroots.ops_intel import scan_signals  # noqa: E402
from freshroots.readiness import OPEN_QUESTIONS  # noqa: E402

OUT = ROOT / "reports"


def md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(r[c]).replace("|", "/").replace("\n", " ") for c in cols) + " |")
    return "\n".join(lines)


def main() -> None:
    cfg = load_config()
    OUT.mkdir(exist_ok=True)
    v = validate(cfg.data_dir)
    a = analyse(v, cfg)

    dd = data_dictionary(v)
    dd.to_csv(OUT / "data_dictionary.csv", index=False)
    v.issues.to_csv(OUT / "validation_findings.csv", index=False)

    rows = []
    for s in v.summaries.values():
        rows.append({"File": s["file"], "Rows": s["rows"], "Rows excluded": s.get("rows_excluded", 0),
                     "Duplicate rows": s["duplicate_rows"], "Unique SKUs": s.get("unique_skus", ""),
                     "Unique distributors": s.get("unique_distributors", ""), "Date range": s.get("date_range", "")})
    issues = v.issues[["file", "line", "column", "severity", "check", "value", "message"]].astype(object).fillna("")
    (OUT / "validation_report.md").write_text(
        "# Data dictionary and validation report\n\n"
        f"Errors: {v.error_count}. Warnings: {v.warning_count}.\n\n"
        "## Files\n\n" + md_table(pd.DataFrame(rows)) + "\n\n"
        "## Join keys\n\n"
        "- weekly_sales.SKU_ID, current_inventory.SKU_ID -> sku_master.SKU_ID\n"
        "- sku_master.Distributor_ID -> distributor_master.Distributor_ID (one distributor per SKU; meaning undefined)\n"
        "- month of each sales week (ISO Thursday) -> calendar.Year_Month\n\n"
        "## Findings\n\n" + md_table(issues) + "\n\n"
        "## Data dictionary\n\n" + md_table(dd.astype(object).fillna("")) + "\n", encoding="utf-8")

    rec = recommendations_frame(a.recommendations)
    rec.to_csv(OUT / "recommendations_example.csv", index=False)

    bt = run_backtest(a.weekly, cfg, horizon=1)
    bt.predictions.to_csv(OUT / "backtest_predictions.csv", index=False)
    s = bt.summary.set_index("method")
    pct = lambda d: d.assign(MAE=d["MAE"].round(2), WAPE=(d["WAPE"] * 100).round(1).astype(str) + "%")  # noqa: E731
    beats = s.at["rules_engine", "WAPE"] < s.at["baseline_12w", "WAPE"]
    (OUT / "backtest_report.md").write_text(
        "# Backtest report\n\n"
        "Chronological, leakage-free evaluation of the weekly demand estimate used by the rules. "
        "Each forecast uses only weeks up to its origin; horizon 1 week.\n\n"
        "Methods:\n\n" + "\n".join(f"- `{k}`: {d}" for k, d in METHODS.items()) + "\n\n"
        "## Summary\n\n" + md_table(pct(bt.summary)) + "\n\n"
        f"The rules-engine estimate **{'beats' if beats else 'does not beat'}** the 12-week baseline "
        f"({s.at['rules_engine', 'WAPE']:.1%} vs {s.at['baseline_12w', 'WAPE']:.1%} WAPE). "
        + ("" if beats else "In this sample, October weeks did not rise 25% for most SKUs, so the festival uplift "
           "overstates demand. Rule A should be reassessed with Raghav before a pilot. ")
        + "\n\n## By target week\n\n" + md_table(pct(bt.by_week)) + "\n\n"
        f"Evaluated SKU-week forecasts per method: {int(s['observations'].iloc[0])}. "
        f"Excluded origins: {len(bt.excluded)} (fewer than {cfg.baseline_weeks} weeks of history).\n\n"
        "## Limits\n\n" + "\n".join(f"- {n}" for n in bt.notes) + "\n"
        "- 15 SKUs x 16 weeks is a small sample; results are indicative only.\n"
        "- Forecast accuracy is not a business outcome. No savings are claimed.\n", encoding="utf-8")

    scan_signals(a.weekly).to_csv(OUT / "operations_signals_history.csv", index=False)

    (OUT / "rules_and_assumptions.md").write_text(
        f"# Rule definitions and prototype assumptions ({RULE_VERSION})\n\n"
        "## Documented rules (from the case)\n\n"
        "- **A. Festival uplift**: in festival months (calendar.csv; October, November, March) the 12-week average weekly "
        "demand is multiplied by 1.25 once, before any cover threshold is checked.\n"
        "- **B. High demand**: average of the latest 4 complete weeks more than 20% above the average of the latest 12 "
        "complete weeks (the 12 include the 4) -> reorder 1.5x Standard_Reorder_Qty.\n"
        "- **C. Stockout risk**: weeks of cover below 6 -> reorder now (standard quantity, 1.5x if also high demand).\n"
        "- **D. Overstock risk**: weeks of cover above 14 -> pause next order.\n"
        "- **E. Perishables** (Perishability = High): below 3 weeks -> replenish; above 4 -> overstock; 3-4 -> within target.\n\n"
        "Weeks of cover = Units_On_Hand (summed across locations) / festival-adjusted weekly demand. "
        "Values exactly on a threshold do not trigger it.\n\n"
        "## Prototype assumptions (not approved Freshroots policy)\n\n"
        "- The analysis date is the inventory As_Of_Date; the planning month is that date's month.\n"
        "- A week belongs to the month of its Thursday (ISO convention).\n"
        "- Perishable windows replace the 6/14-week windows for perishable SKUs (configurable).\n"
        "- Missing sales weeks are not treated as zero; a 4+ week partial average is used for cover only and flagged.\n"
        "- All on-hand stock is treated as usable (no expiry data).\n"
        "- Rule priority:\n" + "\n".join(f"  - {t}: {d}" for t, d in PRIORITY_STEPS) + "\n"
        "- Operations signals (Option C): drop of more than 15% vs the previous 4-week average or week on week, "
        "spike of more than 25%. Open signals block procurement approval for that SKU until acknowledged.\n\n"
        "## Unresolved business questions\n\n" + "\n".join(f"- {q}" for q in OPEN_QUESTIONS) + "\n",
        encoding="utf-8")

    print(f"Wrote reports to {OUT}")
    print(f"Validation: {v.error_count} errors, {v.warning_count} warnings")
    print(f"Recommendations: {len(rec)}; backtest WAPE baseline {s.at['baseline_12w', 'WAPE']:.1%}, "
          f"rules engine {s.at['rules_engine', 'WAPE']:.1%}")


if __name__ == "__main__":
    main()
