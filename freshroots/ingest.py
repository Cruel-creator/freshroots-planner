"""Load and validate the five source CSVs.

Every file is read as text first so nothing is silently coerced. Invalid rows
are never dropped quietly: each problem becomes an Issue (with the CSV line
number), and rows that cannot be used in calculations are marked excluded.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pandas as pd

from .calendar_utils import parse_iso_week, week_end, week_label, week_start

FILES = {
    "weekly_sales": "weekly_sales.csv",
    "sku_master": "sku_master.csv",
    "distributor_master": "distributor_master.csv",
    "current_inventory": "current_inventory.csv",
    "calendar": "calendar.csv",
}

REQUIRED_COLUMNS = {
    "weekly_sales": ["SKU_ID", "Week", "Units_Sold"],
    "sku_master": ["SKU_ID", "SKU_Name", "Category", "Perishability", "Standard_Reorder_Qty",
                   "Unit_of_Measure", "Distributor_ID"],
    "distributor_master": ["Distributor_ID", "Distributor_Name", "Region", "Status"],
    "current_inventory": ["SKU_ID", "Location", "Units_On_Hand", "As_Of_Date"],
    "calendar": ["Year", "Month", "Year_Month", "Is_Festival_Month"],
}

COLUMN_DESCRIPTIONS = {
    ("weekly_sales", "SKU_ID"): "Product identifier; joins to sku_master.SKU_ID.",
    ("weekly_sales", "Week"): "ISO week label (YYYY-Www, Monday-Sunday). One row per SKU per week.",
    ("weekly_sales", "Units_Sold"): "Units sold in the week, aggregated across all distributors (no distributor column).",
    ("sku_master", "SKU_ID"): "Product identifier (primary key).",
    ("sku_master", "SKU_Name"): "Product description.",
    ("sku_master", "Category"): "Product category.",
    ("sku_master", "Perishability"): "Low or High. High = perishable SKU (Rule E applies).",
    ("sku_master", "Standard_Reorder_Qty"): "Standard reorder quantity in units; base for Rule B (1.5x).",
    ("sku_master", "Unit_of_Measure"): "Unit for quantities.",
    ("sku_master", "Distributor_ID"): "One distributor per SKU; joins to distributor_master. Meaning not defined in the case (treated as 'mapped distributor').",
    ("distributor_master", "Distributor_ID"): "Distributor identifier (primary key).",
    ("distributor_master", "Distributor_Name"): "Distributor name.",
    ("distributor_master", "Region"): "State of operation.",
    ("distributor_master", "Status"): "Account status.",
    ("current_inventory", "SKU_ID"): "Product identifier; joins to sku_master.SKU_ID.",
    ("current_inventory", "Location"): "Stocking location. Stock is summed across locations per SKU.",
    ("current_inventory", "Units_On_Hand"): "Units on hand at As_Of_Date. No expiry, in-transit or open-PO data.",
    ("current_inventory", "As_Of_Date"): "Snapshot date (YYYY-MM-DD). Used as the analysis date.",
    ("calendar", "Year"): "Calendar year.",
    ("calendar", "Month"): "Calendar month number (1-12).",
    ("calendar", "Year_Month"): "YYYY-MM key; joins to the month of each sales week.",
    ("calendar", "Is_Festival_Month"): "TRUE/FALSE. TRUE triggers Rule A (+25% demand uplift).",
}

CASE_FESTIVAL_MONTHS = {3, 10, 11}
CASE_REGIONS = {"Maharashtra", "Goa"}


@dataclass
class Issue:
    file: str
    line: int | None          # CSV line number (header = line 1); None for file/cross-file checks
    column: str | None
    severity: str             # error | warning | info
    check: str
    value: str | None
    message: str
    excluded: bool = False    # row excluded from calculations because of this issue


@dataclass
class ValidationResult:
    frames: dict[str, pd.DataFrame]          # typed frames; `excluded` column marks unusable rows
    issues: pd.DataFrame
    summaries: dict[str, dict]
    hashes: dict[str, str]
    missing_files: list[str] = field(default_factory=list)

    def usable(self, name: str) -> pd.DataFrame:
        df = self.frames.get(name)
        if df is None or df.empty:
            return pd.DataFrame()
        return df[~df["excluded"]].copy()

    @property
    def error_count(self) -> int:
        return int((self.issues["severity"] == "error").sum()) if not self.issues.empty else 0

    @property
    def warning_count(self) -> int:
        return int((self.issues["severity"] == "warning").sum()) if not self.issues.empty else 0


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_raw(data_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, str], list[str]]:
    raw, hashes, missing = {}, {}, []
    for name, fname in FILES.items():
        path = Path(data_dir) / fname
        if not path.exists():
            missing.append(fname)
            continue
        raw[name] = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[])
        hashes[fname] = file_sha256(path)
    return raw, hashes, missing


def _line(idx: int) -> int:
    return int(idx) + 2  # header is line 1


def _blank(v) -> bool:
    return v is None or str(v).strip() == ""


def _to_number(v) -> float | None:
    try:
        x = float(str(v).strip())
    except (TypeError, ValueError):
        return None
    if x != x:  # NaN
        return None
    return x


def _infer_type(series: pd.Series) -> str:
    vals = [v for v in series if not _blank(v)]
    if not vals:
        return "empty"
    if all(_to_number(v) is not None for v in vals):
        nums = [_to_number(v) for v in vals]
        return "integer" if all(float(n).is_integer() for n in nums) else "decimal"
    if all(str(v).upper() in {"TRUE", "FALSE"} for v in vals):
        return "boolean"
    if all(parse_iso_week(v) for v in vals):
        return "iso_week"
    try:
        pd.to_datetime(pd.Series(vals), format="%Y-%m-%d", errors="raise")
        return "date"
    except (ValueError, TypeError):
        pass
    try:
        pd.to_datetime(pd.Series(vals), format="%Y-%m", errors="raise")
        return "year_month"
    except (ValueError, TypeError):
        pass
    return "text"


def _summarise(name: str, df: pd.DataFrame) -> dict:
    s: dict = {
        "file": FILES[name],
        "rows": int(len(df)),
        "columns": {c: _infer_type(df[c]) for c in df.columns},
        "missing_values": {c: int(df[c].map(_blank).sum()) for c in df.columns},
        "duplicate_rows": int(df.duplicated().sum()),
    }
    if "SKU_ID" in df.columns:
        s["unique_skus"] = int(df["SKU_ID"].nunique())
    if "Distributor_ID" in df.columns:
        s["unique_distributors"] = int(df["Distributor_ID"].nunique())
    return s


def _check_required(name: str, df: pd.DataFrame, issues: list[Issue]) -> bool:
    missing = [c for c in REQUIRED_COLUMNS[name] if c not in df.columns]
    for c in missing:
        issues.append(Issue(FILES[name], None, c, "error", "required_column",
                            None, f"Required column '{c}' is missing; file cannot be used."))
    extra = [c for c in df.columns if c not in REQUIRED_COLUMNS[name]]
    for c in extra:
        issues.append(Issue(FILES[name], None, c, "info", "extra_column", None,
                            f"Column '{c}' is not used by the prototype."))
    return not missing


def _validate_sales(df: pd.DataFrame, issues: list[Issue]) -> pd.DataFrame:
    f = FILES["weekly_sales"]
    out = df.copy()
    out["excluded"] = False
    out["iso_year"] = pd.NA
    out["iso_week"] = pd.NA
    out["units"] = float("nan")
    for idx, row in out.iterrows():
        if _blank(row["SKU_ID"]):
            issues.append(Issue(f, _line(idx), "SKU_ID", "error", "missing_value", "", "Blank SKU_ID; row excluded.", True))
            out.at[idx, "excluded"] = True
        wk = parse_iso_week(row["Week"])
        if wk is None:
            issues.append(Issue(f, _line(idx), "Week", "error", "invalid_week", str(row["Week"]),
                                "Week is not a valid ISO week (YYYY-Www); row excluded.", True))
            out.at[idx, "excluded"] = True
        else:
            out.at[idx, "iso_year"], out.at[idx, "iso_week"] = wk
        n = _to_number(row["Units_Sold"])
        if n is None:
            issues.append(Issue(f, _line(idx), "Units_Sold", "error", "invalid_number", str(row["Units_Sold"]),
                                "Units_Sold is missing or not numeric; row excluded.", True))
            out.at[idx, "excluded"] = True
        elif n < 0:
            issues.append(Issue(f, _line(idx), "Units_Sold", "error", "negative_value", str(row["Units_Sold"]),
                                "Negative units sold (returns are not modelled); row excluded.", True))
            out.at[idx, "excluded"] = True
        else:
            if not float(n).is_integer():
                issues.append(Issue(f, _line(idx), "Units_Sold", "warning", "non_integer", str(row["Units_Sold"]),
                                    "Fractional units; kept as-is."))
            out.at[idx, "units"] = n

    # Duplicate SKU-week keys: identical duplicates keep one, conflicting ones are all excluded.
    key = out["SKU_ID"].str.strip() + "|" + out["Week"].str.strip()
    for k, grp in out[~out["excluded"]].groupby(key[~out["excluded"]]):
        if len(grp) < 2:
            continue
        same = grp["units"].nunique() == 1
        for i, idx in enumerate(grp.index):
            if same and i == 0:
                continue
            issues.append(Issue(f, _line(idx), "SKU_ID,Week", "error" if not same else "warning",
                                "duplicate_key", k,
                                "Conflicting duplicate SKU-week rows; all excluded." if not same
                                else "Exact duplicate SKU-week row; extra copy excluded.", True))
            out.at[idx, "excluded"] = True
        if not same:
            out.at[grp.index[0], "excluded"] = True
            issues.append(Issue(f, _line(grp.index[0]), "SKU_ID,Week", "error", "duplicate_key", k,
                                "Conflicting duplicate SKU-week rows; all excluded.", True))

    ok = ~out["excluded"]
    out.loc[ok, "week"] = [week_label(int(y), int(w)) for y, w in zip(out.loc[ok, "iso_year"], out.loc[ok, "iso_week"])]
    out.loc[ok, "week_start"] = [week_start(int(y), int(w)) for y, w in zip(out.loc[ok, "iso_year"], out.loc[ok, "iso_week"])]
    out.loc[ok, "week_end"] = [week_end(int(y), int(w)) for y, w in zip(out.loc[ok, "iso_year"], out.loc[ok, "iso_week"])]
    out["SKU_ID"] = out["SKU_ID"].str.strip()
    return out


def _validate_sku_master(df: pd.DataFrame, issues: list[Issue]) -> pd.DataFrame:
    f = FILES["sku_master"]
    out = df.copy()
    out["excluded"] = False
    out["SKU_ID"] = out["SKU_ID"].str.strip()
    out["is_perishable"] = None
    out["standard_qty"] = float("nan")
    dup = out["SKU_ID"].duplicated(keep=False) & (out["SKU_ID"] != "")
    for idx in out.index[dup]:
        issues.append(Issue(f, _line(idx), "SKU_ID", "error", "duplicate_key", out.at[idx, "SKU_ID"],
                            "SKU_ID appears more than once in the master; all copies excluded.", True))
        out.at[idx, "excluded"] = True
    for idx, row in out.iterrows():
        if _blank(row["SKU_ID"]):
            issues.append(Issue(f, _line(idx), "SKU_ID", "error", "missing_value", "", "Blank SKU_ID; row excluded.", True))
            out.at[idx, "excluded"] = True
        for col in ("SKU_Name", "Category", "Unit_of_Measure", "Distributor_ID"):
            if _blank(row[col]):
                issues.append(Issue(f, _line(idx), col, "warning", "missing_value", "", f"Blank {col}."))
        p = str(row["Perishability"]).strip().lower()
        if p == "high":
            out.at[idx, "is_perishable"] = True
        elif p == "low":
            out.at[idx, "is_perishable"] = False
        else:
            issues.append(Issue(f, _line(idx), "Perishability", "error", "invalid_category", str(row["Perishability"]),
                                "Perishability must be Low or High; SKU sent to planner review."))
        q = _to_number(row["Standard_Reorder_Qty"])
        if q is None or q <= 0:
            issues.append(Issue(f, _line(idx), "Standard_Reorder_Qty", "error", "invalid_number",
                                str(row["Standard_Reorder_Qty"]),
                                "Standard reorder quantity missing or not positive; quantity needs planner input."))
        else:
            out.at[idx, "standard_qty"] = q
        uom = str(row["Unit_of_Measure"]).strip()
        if uom and uom != "Units":
            issues.append(Issue(f, _line(idx), "Unit_of_Measure", "warning", "unit_mismatch", uom,
                                "Unit differs from 'Units' used in sales and inventory files."))
    return out


def _validate_distributors(df: pd.DataFrame, issues: list[Issue]) -> pd.DataFrame:
    f = FILES["distributor_master"]
    out = df.copy()
    out["excluded"] = False
    out["Distributor_ID"] = out["Distributor_ID"].str.strip()
    dup = out["Distributor_ID"].duplicated(keep=False)
    for idx in out.index[dup]:
        issues.append(Issue(f, _line(idx), "Distributor_ID", "error", "duplicate_key", out.at[idx, "Distributor_ID"],
                            "Duplicate Distributor_ID; all copies excluded.", True))
        out.at[idx, "excluded"] = True
    for idx, row in out.iterrows():
        region = str(row["Region"]).strip()
        if region and region not in CASE_REGIONS:
            issues.append(Issue(f, _line(idx), "Region", "warning", "case_inconsistency", region,
                                "Case says Freshroots operates in Maharashtra and Goa; this region is outside that scope."))
        status = str(row["Status"]).strip()
        if status != "Active":
            issues.append(Issue(f, _line(idx), "Status", "info", "inactive", status, "Distributor is not Active."))
    return out


def _validate_inventory(df: pd.DataFrame, issues: list[Issue]) -> pd.DataFrame:
    f = FILES["current_inventory"]
    out = df.copy()
    out["excluded"] = False
    out["SKU_ID"] = out["SKU_ID"].str.strip()
    out["units_on_hand"] = float("nan")
    out["as_of"] = pd.NaT
    for idx, row in out.iterrows():
        n = _to_number(row["Units_On_Hand"])
        if n is None:
            issues.append(Issue(f, _line(idx), "Units_On_Hand", "error", "invalid_number", str(row["Units_On_Hand"]),
                                "Units_On_Hand missing or not numeric; row excluded (SKU treated as missing inventory).", True))
            out.at[idx, "excluded"] = True
        elif n < 0:
            issues.append(Issue(f, _line(idx), "Units_On_Hand", "error", "negative_value", str(row["Units_On_Hand"]),
                                "Negative stock; row excluded (SKU treated as missing inventory).", True))
            out.at[idx, "excluded"] = True
        else:
            out.at[idx, "units_on_hand"] = n
        d = pd.to_datetime(str(row["As_Of_Date"]).strip(), format="%Y-%m-%d", errors="coerce")
        if pd.isna(d):
            issues.append(Issue(f, _line(idx), "As_Of_Date", "error", "invalid_date", str(row["As_Of_Date"]),
                                "As_Of_Date is not YYYY-MM-DD; row excluded.", True))
            out.at[idx, "excluded"] = True
        else:
            out.at[idx, "as_of"] = d
    dates = out.loc[~out["excluded"], "as_of"].dropna().unique()
    if len(dates) > 1:
        issues.append(Issue(f, None, "As_Of_Date", "warning", "mixed_snapshot_dates",
                            ", ".join(sorted(str(pd.Timestamp(d).date()) for d in dates)),
                            "Inventory rows have different snapshot dates; the latest is used as analysis date."))
    multi = out[~out["excluded"]].groupby("SKU_ID")["Location"].nunique()
    for sku in multi[multi > 1].index:
        issues.append(Issue(f, None, "Location", "info", "multiple_locations", sku,
                            "SKU stocked at several locations; units are summed."))
    return out


def _validate_calendar(df: pd.DataFrame, issues: list[Issue]) -> pd.DataFrame:
    f = FILES["calendar"]
    out = df.copy()
    out["excluded"] = False
    out["is_festival"] = None
    for idx, row in out.iterrows():
        ym = str(row["Year_Month"]).strip()
        d = pd.to_datetime(ym, format="%Y-%m", errors="coerce")
        if pd.isna(d):
            issues.append(Issue(f, _line(idx), "Year_Month", "error", "invalid_date", ym,
                                "Year_Month is not YYYY-MM; row excluded.", True))
            out.at[idx, "excluded"] = True
            continue
        y, m = _to_number(row["Year"]), _to_number(row["Month"])
        if y != d.year or m != d.month:
            issues.append(Issue(f, _line(idx), "Year,Month", "error", "inconsistent_fields", f"{row['Year']}/{row['Month']} vs {ym}",
                                "Year/Month do not match Year_Month; row excluded.", True))
            out.at[idx, "excluded"] = True
        flag = str(row["Is_Festival_Month"]).strip().upper()
        if flag not in {"TRUE", "FALSE"}:
            issues.append(Issue(f, _line(idx), "Is_Festival_Month", "error", "invalid_boolean", row["Is_Festival_Month"],
                                "Is_Festival_Month must be TRUE or FALSE; row excluded.", True))
            out.at[idx, "excluded"] = True
        else:
            out.at[idx, "is_festival"] = flag == "TRUE"
            if not out.at[idx, "excluded"] and (flag == "TRUE") != (int(d.month) in CASE_FESTIVAL_MONTHS):
                issues.append(Issue(f, _line(idx), "Is_Festival_Month", "warning", "case_inconsistency", f"{ym}={flag}",
                                    "Differs from the case's festival months (October, November, March). calendar.csv is used."))
    dup = out["Year_Month"].duplicated(keep=False)
    for idx in out.index[dup]:
        issues.append(Issue(f, _line(idx), "Year_Month", "error", "duplicate_key", out.at[idx, "Year_Month"],
                            "Duplicate month; all copies excluded.", True))
        out.at[idx, "excluded"] = True
    return out


def _cross_checks(frames: dict[str, pd.DataFrame], issues: list[Issue]) -> None:
    sales, skus = frames.get("weekly_sales"), frames.get("sku_master")
    inv, dists = frames.get("current_inventory"), frames.get("distributor_master")
    master_ids = set(skus.loc[~skus["excluded"], "SKU_ID"]) if skus is not None else set()

    if sales is not None:
        for idx in sales.index[~sales["excluded"] & ~sales["SKU_ID"].isin(master_ids)]:
            issues.append(Issue(FILES["weekly_sales"], _line(idx), "SKU_ID", "warning", "unmatched_reference",
                                sales.at[idx, "SKU_ID"], "SKU not in sku_master; sales kept but no recommendation possible.", True))
            sales.at[idx, "excluded"] = True
        ok = sales[~sales["excluded"]]
        if not ok.empty:
            all_weeks = sorted(set(zip(ok["iso_year"].astype(int), ok["iso_week"].astype(int))),
                               key=lambda t: week_start(*t))
            first, last = week_start(*all_weeks[0]), week_start(*all_weeks[-1])
            expected = []
            d = first
            while d <= last:
                iso = d.isocalendar()
                expected.append(week_label(iso[0], iso[1]))
                d = d + pd.Timedelta(days=7)
            for sku, grp in ok.groupby("SKU_ID"):
                have = set(grp["week"])
                gaps = [w for w in expected if w not in have and w > min(have)]
                if gaps:
                    issues.append(Issue(FILES["weekly_sales"], None, "Week", "warning", "missing_weeks", sku,
                                        f"No sales row for {len(gaps)} week(s): {', '.join(gaps[:6])}"
                                        f"{'...' if len(gaps) > 6 else ''}. Missing weeks are not treated as zero."))
        sku_without_sales = master_ids - set(ok["SKU_ID"])
        for sku in sorted(sku_without_sales):
            issues.append(Issue(FILES["sku_master"], None, "SKU_ID", "warning", "no_sales_history", sku,
                                "SKU has no valid sales rows; demand cannot be calculated."))
        issues.append(Issue(FILES["weekly_sales"], None, None, "info", "granularity",
                            "SKU x week", "Sales are aggregated per SKU; there is no distributor column, so "
                            "distributor-level demand shifts cannot be analysed from this file."))
        n_weeks = ok["week"].nunique() if not ok.empty else 0
        issues.append(Issue(FILES["weekly_sales"], None, None, "info", "sample_scale",
                            f"{ok['SKU_ID'].nunique()} SKUs, {n_weeks} weeks",
                            "The case describes 400 SKUs and 3 years of history; this file is a sample. "
                            "Backtest results are indicative only."))

    if inv is not None:
        for idx in inv.index[~inv["excluded"] & ~inv["SKU_ID"].isin(master_ids)]:
            issues.append(Issue(FILES["current_inventory"], _line(idx), "SKU_ID", "warning", "unmatched_reference",
                                inv.at[idx, "SKU_ID"], "Inventory SKU not in sku_master; row excluded.", True))
            inv.at[idx, "excluded"] = True
        have_inv = set(inv.loc[~inv["excluded"], "SKU_ID"])
        for sku in sorted(master_ids - have_inv):
            issues.append(Issue(FILES["current_inventory"], None, "SKU_ID", "error", "missing_inventory", sku,
                                "No usable inventory row; weeks of cover cannot be calculated."))
        if sales is not None and not sales[~sales["excluded"]].empty and inv.loc[~inv["excluded"], "as_of"].notna().any():
            as_of = inv.loc[~inv["excluded"], "as_of"].max().date()
            last_end = max(sales.loc[~sales["excluded"], "week_end"])
            if (as_of - last_end).days > 7:
                issues.append(Issue(FILES["current_inventory"], None, "As_Of_Date", "warning", "stale_sales",
                                    str(as_of), f"Latest sales week ends {last_end}, more than a week before the inventory snapshot."))
            partial = sales.index[~sales["excluded"] & (sales["week_end"] >= as_of)]
            for idx in partial:
                issues.append(Issue(FILES["weekly_sales"], _line(idx), "Week", "warning", "incomplete_week",
                                    sales.at[idx, "Week"], f"Week has not ended by the inventory date {as_of}; excluded from rule windows.", True))
                sales.at[idx, "excluded"] = True

    if skus is not None and dists is not None:
        dist_ids = set(dists.loc[~dists["excluded"], "Distributor_ID"])
        for idx in skus.index[~skus["excluded"]]:
            d = str(skus.at[idx, "Distributor_ID"]).strip()
            if d and d not in dist_ids:
                issues.append(Issue(FILES["sku_master"], _line(idx), "Distributor_ID", "warning", "unmatched_reference",
                                    d, "Distributor not found in distributor_master."))
        issues.append(Issue(FILES["sku_master"], None, "Distributor_ID", "info", "ambiguous_definition", None,
                            "Each SKU maps to exactly one distributor. The case does not define this field; it is shown "
                            "as 'mapped distributor' and is not used in any calculation."))


def validate(data_dir: Path) -> ValidationResult:
    raw, hashes, missing = read_raw(data_dir)
    issues: list[Issue] = []
    for fname in missing:
        issues.append(Issue(fname, None, None, "error", "missing_file", None, "File not found; dependent calculations disabled."))

    validators = {
        "weekly_sales": _validate_sales,
        "sku_master": _validate_sku_master,
        "distributor_master": _validate_distributors,
        "current_inventory": _validate_inventory,
        "calendar": _validate_calendar,
    }
    frames: dict[str, pd.DataFrame] = {}
    summaries: dict[str, dict] = {}
    for name, df in raw.items():
        summaries[name] = _summarise(name, df)
        if _check_required(name, df, issues):
            frames[name] = validators[name](df, issues)
    _cross_checks(frames, issues)

    sales = frames.get("weekly_sales")
    if sales is not None and (~sales["excluded"]).any():
        ok = sales[~sales["excluded"]]
        summaries["weekly_sales"]["date_range"] = (
            f"{min(ok['week'])} to {max(ok['week'])} "
            f"({min(ok['week_start'])} to {max(ok['week_end'])})"
        )
        summaries["weekly_sales"]["weeks"] = int(ok["week"].nunique())
    inv = frames.get("current_inventory")
    if inv is not None and inv["as_of"].notna().any():
        summaries["current_inventory"]["date_range"] = ", ".join(
            sorted({str(pd.Timestamp(d).date()) for d in inv["as_of"].dropna()}))
    cal = frames.get("calendar")
    if cal is not None and not cal.empty:
        summaries["calendar"]["date_range"] = f"{cal['Year_Month'].min()} to {cal['Year_Month'].max()}"
        summaries["calendar"]["festival_months"] = sorted(cal.loc[cal["is_festival"] == True, "Year_Month"].tolist())  # noqa: E712

    for name, frame in frames.items():
        summaries[name]["rows_excluded"] = int(frame["excluded"].sum())

    issues_df = pd.DataFrame([vars(i) for i in issues],
                             columns=["file", "line", "column", "severity", "check", "value", "message", "excluded"])
    sev_order = {"error": 0, "warning": 1, "info": 2}
    if not issues_df.empty:
        issues_df = issues_df.sort_values(by=["severity", "file", "line"],
                                          key=lambda s: s.map(sev_order) if s.name == "severity" else s,
                                          na_position="first").reset_index(drop=True)
        issues_df["line"] = issues_df["line"].astype("Int64")
    return ValidationResult(frames, issues_df, summaries, hashes, missing)


def data_dictionary(result: ValidationResult) -> pd.DataFrame:
    rows = []
    for name, s in result.summaries.items():
        frame = result.frames.get(name)
        for col, typ in s["columns"].items():
            example = ""
            unique = None
            if frame is not None and col in frame.columns:
                vals = frame[col][frame[col].map(lambda v: not _blank(v))]
                example = str(vals.iloc[0]) if len(vals) else ""
                unique = int(vals.nunique())
            rows.append({
                "file": FILES[name],
                "column": col,
                "observed_type": typ,
                "missing": s["missing_values"].get(col, 0),
                "unique_values": unique,
                "example": example,
                "description": COLUMN_DESCRIPTIONS.get((name, col), "Not used by the prototype."),
            })
    return pd.DataFrame(rows)
