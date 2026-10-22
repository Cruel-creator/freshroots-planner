"""CSV exports: recommendations, draft purchase orders, validation errors."""
from __future__ import annotations

import math
from datetime import datetime, timezone

import pandas as pd

DRAFT_BANNER = "DRAFT - NOT SUBMITTED. Prototype output for procurement review; enter in Zoho Inventory manually."

RECOMMENDATION_COLUMNS = [
    ("sku_id", "SKU_ID"), ("sku_name", "SKU_Name"), ("category", "Category"), ("perishability", "Perishability"),
    ("scope", "Scope"), ("mapped_distributor", "Mapped_Distributor"),
    ("recent_4w_units", "Recent_4w_Units"), ("recent_4w_avg", "Recent_4w_Avg_Weekly"),
    ("baseline_12w_avg", "Baseline_12w_Avg_Weekly"), ("demand_change_pct", "Demand_Change_Pct"),
    ("festival_uplift_applied", "Festival_Uplift_Applied"), ("adjusted_weekly_demand", "Adjusted_Weekly_Demand"),
    ("current_stock", "Current_Stock"), ("inventory_as_of", "Inventory_As_Of"), ("weeks_of_cover", "Weeks_Of_Cover"),
    ("flags", "Flags"), ("conflicts", "Conflicts"), ("action", "Recommended_Action"),
    ("standard_qty", "Standard_Reorder_Qty"), ("recommended_qty", "Recommended_Qty"), ("qty_basis", "Qty_Basis"),
    ("priority_step", "Priority_Step"), ("explanation", "Reason"), ("data_quality_status", "Data_Quality_Status"),
    ("exception_codes", "Exceptions"), ("status", "Approval_Status"), ("final_action", "Final_Action"),
    ("final_qty", "Final_Qty"), ("planner_reason", "Planner_Reason"), ("rule_version", "Rule_Version"),
    ("run_id", "Run_ID"), ("source_weeks", "Source_Weeks"),
]


def _cell(v):
    if isinstance(v, list):
        return "; ".join(map(str, v))
    if isinstance(v, float) and math.isinf(v):
        return "inf"
    return v


def recommendations_frame(recs: pd.DataFrame) -> pd.DataFrame:
    cols = [(src, dst) for src, dst in RECOMMENDATION_COLUMNS if src in recs.columns]
    out = recs[[s for s, _ in cols]].copy()
    out.columns = [d for _, d in cols]
    return out.apply(lambda col: col.map(_cell))


def draft_po_frame(approved: pd.DataFrame, run_id: str, exported_by: str) -> pd.DataFrame:
    ts = datetime.now(timezone.utc)
    po_id = "DRAFT-PO-" + ts.strftime("%Y%m%d-%H%M%S")
    rows = []
    for i, r in enumerate(approved.sort_values("sku_id").itertuples(), start=1):
        rows.append({
            "Draft_PO_ID": po_id,
            "Line": i,
            "Status": "DRAFT - NOT SUBMITTED",
            "SKU_ID": r.sku_id,
            "SKU_Name": r.sku_name,
            "Quantity": r.final_qty,
            "Unit": getattr(r, "unit", "Units"),
            "Action": r.final_action,
            "Supplier": "NOT IN SOURCE DATA - procurement to fill",
            "Unit_Price": "NOT IN SOURCE DATA",
            "Requested_Delivery": "NOT IN SOURCE DATA (no lead times)",
            "Planner_Decision": r.planner_decision,
            "Planner_Reason": r.planner_reason or "",
            "Recommendation_ID": r.rec_id,
            "Run_ID": run_id,
            "Exported_By": exported_by,
            "Exported_At_UTC": ts.isoformat(timespec="seconds"),
            "Note": DRAFT_BANNER,
        })
    return pd.DataFrame(rows)


def to_csv_bytes(df: pd.DataFrame, banner: str | None = None) -> bytes:
    body = df.to_csv(index=False)
    if banner:
        body = f"# {banner}\n" + body
    return body.encode("utf-8")
