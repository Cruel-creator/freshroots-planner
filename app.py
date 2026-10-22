"""Freshroots demand-planning prototype. Launch: streamlit run app.py"""
from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from freshroots import ops_intel as OI
from freshroots import readiness as RD
from freshroots import rules as R
from freshroots import workflow as W
from freshroots.backtest import METHODS, run_backtest
from freshroots.config import RULE_VERSION, load_config
from freshroots.engine import ACTION_REVIEW, ALL_ACTIONS, PRIORITY_STEPS, REORDER_ACTIONS, analyse
from freshroots.exports import DRAFT_BANNER, recommendations_frame, to_csv_bytes
from freshroots.ingest import FILES, data_dictionary, file_sha256, validate
from freshroots.store import Store

st.set_page_config(page_title="Freshroots Demand Planning", layout="wide")

GREEN, GREEN_SOFT, AMBER, RED, BLUE, GREY = "#1F7A4D", "#CFE5D8", "#B7791F", "#B42318", "#2F6690", "#8A948D"
STATUS_COLORS = {
    W.GENERATED: "#EEF0EF", W.PENDING_PLANNER: "#FCF0D9", W.PLANNER_APPROVED: "#DCEFE3",
    W.PLANNER_OVERRIDDEN: "#E3ECF5", W.PENDING_PROCUREMENT: "#FCF0D9", W.PROCUREMENT_APPROVED: "#CFE5D8",
    W.REJECTED: "#F8DEDB", W.EXPORTED_DRAFT: "#E4E7E5",
}

st.markdown("""
<style>
.block-container {padding-top: 2.2rem; max-width: 1400px;}
h1, h2, h3 {letter-spacing: -0.01em;}
div[data-testid="stMetric"] {background: #FFFFFF; border: 1px solid #DDE3DF; border-radius: 8px; padding: 10px 14px;}
div[data-testid="stMetricLabel"] p {font-size: 0.8rem; color: #4A554E;}
.fr-note {font-size: 0.82rem; color: #4A554E;}
.fr-card {background:#FFFFFF; border:1px solid #DDE3DF; border-radius:8px; padding:12px 14px; margin-bottom:10px; font-size:0.88rem;}
.fr-card h4 {margin:0 0 6px 0; font-size:0.9rem; padding:0;}
.fr-badge {display:inline-block; padding:2px 8px; border-radius:10px; font-size:0.75rem; font-weight:600;}
.fr-group {font-weight:700; font-size:1.0rem; margin-bottom:0;}
.fr-sub {font-style:italic; font-size:0.8rem; color:#4A554E; margin-bottom:8px;}
.fr-label {font-size:0.72rem; text-transform:uppercase; letter-spacing:0.04em; color:#6B756F; margin-top:8px;}
</style>
""", unsafe_allow_html=True)

CFG = load_config()


# ---------------------------------------------------------------- data ------
def input_hashes() -> dict:
    return {f: file_sha256(CFG.data_dir / f) for f in FILES.values() if (CFG.data_dir / f).exists()}


@st.cache_data(show_spinner="Validating source files...")
def load_analysis(data_dir: str, hashes_key: tuple):
    v = validate(CFG.data_dir)
    return v, analyse(v, CFG)


@st.cache_data(show_spinner=False)
def load_backtest(hashes_key: tuple, horizon: int):
    _, a = load_analysis(str(CFG.data_dir), hashes_key)
    return run_backtest(a.weekly, CFG, horizon=horizon)


@st.cache_resource
def get_store() -> Store:
    return Store(CFG.db_path)


HASHES = input_hashes()
HKEY = tuple(sorted(HASHES.items()))
V, A = load_analysis(str(CFG.data_dir), HKEY)
STORE = get_store()

if STORE.latest_run_id() is None and not A.recommendations.empty:
    W.create_run(STORE, A, CFG, HASHES, W.Actor("system (first launch)", W.SYSTEM))


def val(x):
    """None for missing values; DataFrames turn stored NULLs into NaN, which is truthy."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    return x


def fmt_num(x, digits=1):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    if isinstance(x, float) and math.isinf(x):
        return "no demand"
    return f"{x:,.{digits}f}"


def flag_text(flags) -> str:
    return ", ".join(R.FLAG_LABELS.get(f, f) for f in flags if f != R.FESTIVAL_UPLIFT) or "None"


def human_checkpoints(row) -> str:
    """Which Boundary check puts a human on this line (07 failure risk, 08 judgment)."""
    points = ["08 Raghav: exception review" if row.get("needs_review") else "Raghav: sign-off"]
    if row.get("final_action") in REORDER_ACTIONS or row.get("action") in REORDER_ACTIONS or row.get("action") == ACTION_REVIEW:
        points.append("07 Procurement: PO approval")
    return " | ".join(points)


def style_status(df: pd.DataFrame, col: str = "Status"):
    return df.style.map(lambda s: f"background-color: {STATUS_COLORS.get(s, '#FFFFFF')}", subset=[col])


def chart_layout(fig, height=320):
    fig.update_layout(template="plotly_white", height=height, margin=dict(l=10, r=10, t=48, b=10),
                      font=dict(size=12), legend=dict(orientation="h", y=-0.22), title_font=dict(size=14))
    return fig


# ------------------------------------------------------------- sidebar ------
with st.sidebar:
    st.markdown("### Freshroots")
    st.caption("Demand planning prototype")
    labels = [f"{a.name} ({a.role})" for a in W.DEFAULT_ACTORS]
    actor_label = st.selectbox("Acting as", labels, index=0,
                               help="Prototype: no authentication. The selected identity is written to the audit log.")
    ACTOR = W.DEFAULT_ACTORS[labels.index(actor_label)]

    runs = STORE.runs()
    run_ids = runs["run_id"].tolist() if not runs.empty else []
    RUN_ID = st.selectbox("Recommendation run", run_ids, index=0) if run_ids else None
    if st.button("Generate new run", width="stretch",
                 help="Recomputes recommendations from the current files and starts a new approval cycle."):
        rid = W.create_run(STORE, A, CFG, HASHES, ACTOR)
        st.toast(f"Created {rid}")
        st.rerun()
    if RUN_ID:
        run_meta = STORE.run(RUN_ID)
        st.caption(f"Rule version: {run_meta['rule_version']}  \nCreated {run_meta['created_at']} by {run_meta['created_by']}")
        if json.loads(run_meta["input_hashes_json"]) != HASHES:
            st.warning("Source files changed since this run. Generate a new run to use the current data.")
    st.divider()
    st.caption(f"Inventory as of: {A.analysis_date}  \nLatest complete sales week: {A.anchor_week}  \n"
               f"Planning month {A.planning_month}: {'festival month' if A.planning_month_festival else 'not a festival month'}")
    st.caption("No SAP or Zoho connection. Nothing is submitted externally.")

RECS = STORE.recs(RUN_ID) if RUN_ID else pd.DataFrame()
if not RECS.empty:
    RECS["checkpoints"] = RECS.apply(human_checkpoints, axis=1)


def require_run() -> bool:
    if RECS.empty:
        st.info("No recommendation run yet. Check the Data Quality page: required files may be missing.")
        return False
    return True


def run_action(fn, ok_msg: str):
    try:
        fn()
        st.session_state["flash"] = ("success", ok_msg)
    except (W.WorkflowError, RuntimeError) as e:
        st.session_state["flash"] = ("error", str(e))
    st.rerun()


def show_flash():
    if "flash" in st.session_state:
        kind, msg = st.session_state.pop("flash")
        (st.success if kind == "success" else st.error)(msg)


def demand_chart(sku: str, weeks: list[str] | None = None, height: int = 340):
    full = A.weekly[A.weekly["SKU_ID"] == sku].sort_values("week_start").copy()
    full["trailing_12w_avg"] = full["units"].rolling(CFG.baseline_weeks, min_periods=CFG.baseline_weeks).mean()
    if weeks is not None:
        full = full[full["week"].isin(weeks)]
    fig = go.Figure()
    fig.add_bar(x=full["week"], y=full["units"], name="Actual weekly units",
                marker_color=[GREEN if f else "#9BC5AE" for f in full["is_festival"].fillna(False)])
    fig.add_scatter(x=full["week"], y=full["trailing_12w_avg"], name="Trailing 12-week average (baseline)",
                    line=dict(color="#18201B", width=2))
    rec = RECS[RECS["sku_id"] == sku]
    if not rec.empty and val(rec["adjusted_weekly_demand"].iloc[0]) is not None:
        fig.add_hline(y=rec["adjusted_weekly_demand"].iloc[0], line_dash="dash", line_color=AMBER,
                      annotation_text="Festival-adjusted demand used for cover", annotation_position="top left")
    fig.update_layout(title=f"{sku}: weekly sales vs 12-week baseline (darker bars: festival-month weeks)")
    st.plotly_chart(chart_layout(fig, height), width="stretch")


# ------------------------------------------------------------- pages --------
def page_overview():
    st.title("Executive overview")
    st.caption(f"Run {RUN_ID} | Inventory as of {A.analysis_date} | Rules {RULE_VERSION}")
    if not require_run():
        return
    r = RECS
    flags = r["flags"]
    perish_out = int(flags.map(lambda f: R.PERISHABLE_REPLENISH_RISK in f or R.PERISHABLE_OVERSTOCK_RISK in f).sum())
    awaiting = int(r["status"].isin([W.PENDING_PLANNER, W.PENDING_PROCUREMENT]).sum())
    cols = st.columns(4)
    cols[0].metric("SKUs analysed", len(r))
    cols[1].metric("High demand", int(flags.map(lambda f: R.HIGH_DEMAND in f).sum()), help="Last 4 weeks > 20% above 12-week average")
    cols[2].metric("Stockout risk", int(flags.map(lambda f: R.STOCKOUT_RISK in f).sum()), help="Non-perishable, cover < 6 weeks")
    cols[3].metric("Overstock risk", int(flags.map(lambda f: R.OVERSTOCK_RISK in f).sum()), help="Non-perishable, cover > 14 weeks")
    cols = st.columns(4)
    cols[0].metric("Perishables outside 3-4 wks", perish_out)
    cols[1].metric("Awaiting review", awaiting, help="Pending planner review or procurement approval")
    cols[2].metric("Data errors", V.error_count, help="Validation errors; see the Data quality page")
    cols[3].metric("Data warnings", V.warning_count, help="Validation warnings; see the Data quality page")

    short = pd.to_numeric(r["shortfall_to_min_cover_units"], errors="coerce").sum()
    excess = pd.to_numeric(r["excess_over_max_cover_units"], errors="coerce").sum()
    with st.container(border=True):
        st.markdown("**Estimated impact indicators**: projections from today's stock vs thresholds, not realised savings")
        c1, c2, c3 = st.columns(3)
        c1.metric("Units short of minimum cover", f"{short:,.0f}")
        c2.metric("Units above maximum cover", f"{excess:,.0f}")
        c3.metric("Reported loss baseline (case)", "Rs 28-34L / qtr")
        st.markdown('<div class="fr-note">No prices exist in the data, so unit gaps cannot be converted to rupees. '
                    'Rupee savings can only be established in the parallel pilot.</div>', unsafe_allow_html=True)

    left, right = st.columns(2)
    wk = A.weekly.groupby(["week", "week_start", "is_festival"], as_index=False)["units"].sum().sort_values("week_start")
    fig = go.Figure()
    fig.add_bar(x=wk["week"], y=wk["units"], name="Units sold",
                marker_color=[GREEN if f else "#9BC5AE" for f in wk["is_festival"].fillna(False)])
    fig.update_layout(title="Weekly sales, all SKUs (darker: festival-month weeks per calendar.csv)")
    left.plotly_chart(chart_layout(fig), width="stretch")

    cov = r[["sku_id", "weeks_of_cover", "is_perishable"]].copy()
    cov["weeks_of_cover"] = pd.to_numeric(cov["weeks_of_cover"], errors="coerce").replace([np.inf], np.nan)
    cov["Type"] = np.where(cov["is_perishable"] == True, "Perishable (3-4 wks)", "Standard (6-14 wks)")  # noqa: E712
    fig = px.bar(cov.sort_values("weeks_of_cover"), x="sku_id", y="weeks_of_cover", color="Type",
                 color_discrete_map={"Perishable (3-4 wks)": AMBER, "Standard (6-14 wks)": GREEN},
                 title="Weeks of cover by SKU (festival-adjusted demand)",
                 labels={"sku_id": "SKU", "weeks_of_cover": "Weeks of cover"})
    for y, c in [(CFG.stockout_weeks, RED), (CFG.overstock_weeks, BLUE)]:
        fig.add_hline(y=y, line_dash="dot", line_color=c, annotation_text=f"{y:g} wks", annotation_position="right")
    for y in (CFG.perishable_min_weeks, CFG.perishable_max_weeks):
        fig.add_hline(y=y, line_dash="dash", line_color=AMBER, opacity=0.6)
    right.plotly_chart(chart_layout(fig), width="stretch")

    left, right = st.columns(2)
    flag_codes = [R.HIGH_DEMAND, R.STOCKOUT_RISK, R.OVERSTOCK_RISK, R.PERISHABLE_REPLENISH_RISK,
                  R.PERISHABLE_OVERSTOCK_RISK, R.PERISHABLE_WITHIN_TARGET]
    mat = pd.DataFrame([[1 if f in fl else 0 for f in flag_codes] for fl in r["flags"]],
                       index=r["sku_id"], columns=[R.FLAG_LABELS[f] for f in flag_codes])
    fig = go.Figure(go.Heatmap(z=mat.values, x=mat.columns, y=mat.index, colorscale=[[0, "#F1F4F2"], [1, GREEN]],
                               showscale=False, xgap=2, ygap=2, hovertemplate="%{y}: %{x}<extra></extra>"))
    fig.update_layout(title="Risk flags by SKU")
    fig.update_yaxes(autorange="reversed")
    left.plotly_chart(chart_layout(fig, 440), width="stretch")

    cat = r.groupby(["category", "action"], as_index=False).size()
    fig = px.bar(cat, x="category", y="size", color="action", title="Recommendations by category",
                 color_discrete_map={"Reorder now": RED, "Reorder (high demand)": AMBER, "Pause next order": BLUE,
                                     "No action": GREEN_SOFT, ACTION_REVIEW: "#5B5F97"},
                 labels={"size": "SKUs", "category": "Category", "action": "Action"})
    right.plotly_chart(chart_layout(fig, 440), width="stretch")

    sku = st.selectbox("Historical demand vs baseline", r["sku_id"] + " " + r["sku_name"], key="ov_sku").split(" ")[0]
    demand_chart(sku)


def page_demand():
    st.title("Demand planning")
    if not require_run():
        return
    r = RECS.copy()
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        q = c1.text_input("Search SKU or name", placeholder="e.g. SKU004 or almond")
        dist = c2.multiselect("Mapped distributor", sorted(r["mapped_distributor"].unique()),
                              help="From sku_master.Distributor_ID. Sales are not split by distributor in the data.")
        cats = c3.multiselect("Category", sorted(r["category"].unique()))
        stat = c4.multiselect("Approval status", W.STATUSES)
        c5, c6, c7 = st.columns([2, 1, 3])
        flag_opts = [R.HIGH_DEMAND, R.STOCKOUT_RISK, R.OVERSTOCK_RISK, R.PERISHABLE_REPLENISH_RISK,
                     R.PERISHABLE_OVERSTOCK_RISK, R.PERISHABLE_WITHIN_TARGET]
        flg = c5.multiselect("Flags", flag_opts, format_func=lambda f: R.FLAG_LABELS[f])
        perish = c6.toggle("Perishable only")
        weeks = sorted(A.weekly["week"].unique())
        wr = c7.select_slider("Chart date range", options=weeks, value=(weeks[0], weeks[-1]),
                              help="Affects charts only. Rules always use the latest 4 and 12 complete weeks.")
    if q:
        ql = q.lower()
        r = r[r["sku_id"].str.lower().str.contains(ql, regex=False) | r["sku_name"].str.lower().str.contains(ql, regex=False)]
    if dist:
        r = r[r["mapped_distributor"].isin(dist)]
    if cats:
        r = r[r["category"].isin(cats)]
    if stat:
        r = r[r["status"].isin(stat)]
    if flg:
        r = r[r["flags"].map(lambda f: any(x in f for x in flg))]
    if perish:
        r = r[r["is_perishable"] == True]  # noqa: E712

    table = pd.DataFrame({
        "SKU": r["sku_id"], "Name": r["sku_name"], "Category": r["category"], "Perishability": r["perishability"],
        "4-wk avg": r["recent_4w_avg"], "12-wk avg": r["baseline_12w_avg"],
        "Change %": pd.to_numeric(r["demand_change_pct"], errors="coerce") * 100,
        "Adj. demand/wk": r["adjusted_weekly_demand"], "Stock": r["current_stock"],
        "Weeks of cover": pd.to_numeric(r["weeks_of_cover"], errors="coerce").replace([np.inf], np.nan),
        "Flags": r["flags"].map(flag_text), "Action": r["action"], "Qty": r["recommended_qty"],
        "Review": r["needs_review"].map(lambda b: "Yes" if b else ""), "Status": r["status"],
    }).reset_index(drop=True)
    st.caption(f"{len(table)} of {len(RECS)} SKUs. Select a row for the drill-down; click a header to sort.")
    ev = st.dataframe(
        style_status(table), hide_index=True, width="stretch", on_select="rerun", selection_mode="single-row",
        key="demand_table",
        column_config={
            "4-wk avg": st.column_config.NumberColumn(format="%.1f"),
            "12-wk avg": st.column_config.NumberColumn(format="%.1f"),
            "Change %": st.column_config.NumberColumn(format="%+.1f%%", help="4-wk avg / 12-wk avg - 1"),
            "Adj. demand/wk": st.column_config.NumberColumn(format="%.1f", help="12-wk avg x 1.25 in festival months"),
            "Stock": st.column_config.NumberColumn(format="%d"),
            "Weeks of cover": st.column_config.NumberColumn(format="%.2f", help="Stock / adjusted weekly demand"),
            "Qty": st.column_config.NumberColumn(format="%d"),
        })
    rows = ev.selection.rows if ev and ev.selection else []
    if table.empty:
        return
    sku = table.iloc[rows[0]]["SKU"] if rows else table.iloc[0]["SKU"]
    rec = RECS[RECS["sku_id"] == sku].iloc[0]
    st.subheader(f"{sku} - {rec['sku_name']}")
    st.caption(f"{rec['scope']} | Mapped distributor: {rec['mapped_distributor']} | Status: {rec['status']}")
    m = st.columns(6)
    m[0].metric("4-week avg", fmt_num(rec["recent_4w_avg"]))
    m[1].metric("12-week avg", fmt_num(rec["baseline_12w_avg"]))
    m[2].metric("Adjusted demand / wk", fmt_num(rec["adjusted_weekly_demand"]))
    m[3].metric("Current stock", fmt_num(rec["current_stock"], 0))
    m[4].metric("Weeks of cover", fmt_num(rec["weeks_of_cover"], 2))
    m[5].metric("Recommended qty", fmt_num(rec["recommended_qty"], 0) if val(rec["recommended_qty"]) is not None else "Planner input")
    left, right = st.columns([3, 2])
    with left:
        sel = [w for w in weeks if wr[0] <= w <= wr[1]]
        demand_chart(sku, sel, 330)
    with right:
        st.markdown(f"**Recommendation:** {rec['action']}  \n**Quantity basis:** {rec['qty_basis']}")
        st.markdown(rec["explanation"])
        if rec["conflicts"]:
            st.warning("Conflict: " + " ".join(rec["conflicts"]))
        st.markdown(f"**Data quality:** {rec['data_quality_status']}")
        change = rec["demand_change_pct"]
        with st.expander("Formulas used"):
            st.markdown(f"""
- 4-week average = units in {rec['source_weeks'][-CFG.recent_weeks]}..{rec['source_weeks'][-1]} / {CFG.recent_weeks}
- 12-week average = units in {rec['source_weeks'][0]}..{rec['source_weeks'][-1]} / {CFG.baseline_weeks}
- Demand change = 4-week avg / 12-week avg - 1 = {fmt_num(change * 100 if change is not None else None)}% (high demand if more than {CFG.high_demand_threshold:.0%})
- Adjusted demand = 12-week avg x {1 + CFG.festival_uplift:.2f} when the planning month ({rec['planning_month']}) is a festival month in calendar.csv
- Weeks of cover = usable stock / adjusted demand = {fmt_num(rec['current_stock'], 0)} / {fmt_num(rec['adjusted_weekly_demand'])} = {fmt_num(rec['weeks_of_cover'], 2)}
- Thresholds: {'perishable window 3-4 weeks' if rec['is_perishable'] else 'stockout below 6, overstock above 14 weeks'}
- Reorder quantity = standard reorder qty ({fmt_num(rec['standard_qty'], 0)}) x 1.5 when high demand
""")
        src = A.weekly[(A.weekly["SKU_ID"] == sku) & (A.weekly["week"].isin(rec["source_weeks"]))][["week", "units", "month", "is_festival"]]
        with st.expander("Source rows (weekly_sales.csv)"):
            st.dataframe(src, hide_index=True, width="stretch")


def review_controls(rec, key_prefix: str):
    """Planner / procurement controls for one recommendation. The workflow module enforces the rules."""
    status, rid = rec["status"], rec["rec_id"]
    if status == W.PENDING_PLANNER:
        if ACTOR.role != W.PLANNER:
            st.info("Waiting for Raghav (planner). Switch 'Acting as' in the sidebar to review.")
            return
        can_approve = rec["action"] != ACTION_REVIEW and not (rec["action"] in REORDER_ACTIONS and not val(rec["recommended_qty"]))
        if st.button("Approve as recommended", key=f"{key_prefix}_ap_{rid}", disabled=not can_approve, type="primary",
                     help=None if can_approve else "Blocked: no single rule answer or missing quantity. Use override."):
            run_action(lambda: W.planner_approve(STORE, rid, ACTOR), f"Approved {rec['sku_id']}")
        with st.form(f"{key_prefix}_ov_{rid}", border=True):
            st.markdown("**Override or reject** (reason required, min. 10 characters)")
            o1, o2 = st.columns(2)
            act = o1.selectbox("Action", [a for a in ALL_ACTIONS if a != ACTION_REVIEW], key=f"{key_prefix}_act_{rid}")
            default_q = float(val(rec["recommended_qty"]) or val(rec.get("max_qty_within_window")) or 0)
            qty = o2.number_input("Quantity (units)", min_value=0.0, step=10.0, value=default_q, key=f"{key_prefix}_q_{rid}")
            reason = st.text_area("Reason", key=f"{key_prefix}_r_{rid}", placeholder="Why the rule output is being changed")
            b1, b2 = st.columns(2)
            if b1.form_submit_button("Save override"):
                run_action(lambda: W.planner_override(STORE, rid, ACTOR, action=act, qty=qty, reason=reason),
                           f"Override saved for {rec['sku_id']}")
            if b2.form_submit_button("Reject recommendation"):
                run_action(lambda: W.reject(STORE, rid, ACTOR, reason), f"Rejected {rec['sku_id']}")
    elif status == W.PENDING_PROCUREMENT:
        open_sig = W.open_signals_for(STORE, RUN_ID, rec["sku_id"])
        if not open_sig.empty:
            st.warning(f"Operations signal open for {rec['sku_id']}: " + "; ".join(open_sig["message"]) +
                       ". Approval is blocked until it is triaged and acknowledged (Operations intelligence page).")
        if ACTOR.role != W.PROCUREMENT:
            st.info("Waiting for procurement approval. Switch 'Acting as' to the procurement role.")
            return
        with st.form(f"{key_prefix}_pr_{rid}"):
            st.markdown(f"**Procurement decision:** {rec['final_action']}, {fmt_num(rec['final_qty'], 0)} units")
            reason = st.text_input("Reason (required to reject)", key=f"{key_prefix}_prr_{rid}")
            b1, b2 = st.columns(2)
            if b1.form_submit_button("Approve PO line", type="primary"):
                run_action(lambda: W.procurement_approve(STORE, rid, ACTOR), f"Approved PO line {rec['sku_id']}")
            if b2.form_submit_button("Reject"):
                run_action(lambda: W.reject(STORE, rid, ACTOR, reason), f"Rejected {rec['sku_id']}")
    else:
        st.caption(f"Status: {status}. No action available.")


def page_exceptions():
    st.title("Exception review")
    st.caption("Assigned to Raghav Kulkarni. Exceptions come from deterministic statistical checks and rule conflicts; "
               "they never change a calculation. AI explanations: " +
               ("disabled (no provider configured)." if CFG.llm_provider == "disabled"
                else f"provider '{CFG.llm_provider}' is shown in the web UI's Exceptions page only."))
    show_flash()
    if not require_run():
        return
    exc = A.exceptions
    review = RECS[RECS["needs_review"].astype(bool)]
    c = st.columns(4)
    c[0].metric("SKUs needing review", len(review))
    c[1].metric("Exceptions", len(exc))
    c[2].metric("Rule conflicts", int((exc["code"] == "RULE_CONFLICT").sum()) if not exc.empty else 0)
    c[3].metric("Still pending planner", int((review["status"] == W.PENDING_PLANNER).sum()))
    if review.empty:
        st.success("No exceptions in this run.")
        return
    cat_filter = st.multiselect("Exception category", sorted(exc["category"].unique()) if not exc.empty else [])
    for _, rec in review.iterrows():
        e = exc[exc["sku_id"] == rec["sku_id"]]
        if cat_filter and not e["category"].isin(cat_filter).any():
            continue
        with st.expander(f"{rec['sku_id']} - {rec['sku_name']} | {rec['action']} | {rec['status']}",
                         expanded=rec["status"] == W.PENDING_PLANNER):
            for _, x in e.iterrows():
                st.markdown(f"**{x['category']}** ({x['code']})")
                a1, a2 = st.columns(2)
                a1.markdown(f'<div class="fr-label">Triggering signal</div>{x["signal"]}'
                            f'<div class="fr-label">Source data</div>{x["source_data"]}'
                            f'<div class="fr-label">Rules triggered</div>{x["rules_triggered"]}', unsafe_allow_html=True)
                a2.markdown(f'<div class="fr-label">Why automation is not enough</div>{x["why_not_automated"]}'
                            f'<div class="fr-label">Suggested next action</div>{x["suggested_action"]}', unsafe_allow_html=True)
                st.divider()
            st.markdown(f"**Rule output:** {rec['explanation']}")
            review_controls(rec, "exc")


def page_workbench():
    st.title("Replenishment workbench")
    st.caption("Raghav signs off every line (Check 08). Procurement approves every purchase-order line (Check 07). "
               "Export produces a draft file only; nothing is sent to Zoho or SAP.")
    show_flash()
    if not require_run():
        return
    r = RECS
    c = st.columns(5)
    for i, s in enumerate([W.PENDING_PLANNER, W.PENDING_PROCUREMENT, W.PROCUREMENT_APPROVED, W.REJECTED, W.EXPORTED_DRAFT]):
        c[i].metric(s, int((r["status"] == s).sum()))

    table = pd.DataFrame({
        "SKU": r["sku_id"], "Name": r["sku_name"], "Action": r["action"],
        "Rec. qty": r["recommended_qty"], "Final action": r["final_action"], "Final qty": r["final_qty"],
        "Cover (wks)": pd.to_numeric(r["weeks_of_cover"], errors="coerce").replace([np.inf], np.nan),
        "Flags": r["flags"].map(flag_text), "Conflicts": r["conflicts"].map(lambda c: " ".join(c)),
        "Human checkpoints": r["checkpoints"], "Status": r["status"],
    })
    st.dataframe(style_status(table), hide_index=True, width="stretch",
                 column_config={"Rec. qty": st.column_config.NumberColumn(format="%d"),
                                "Final qty": st.column_config.NumberColumn(format="%d"),
                                "Cover (wks)": st.column_config.NumberColumn(format="%.2f")})

    if ACTOR.role == W.PLANNER:
        clean = r[(r["status"] == W.PENDING_PLANNER) & (~r["needs_review"].astype(bool)) & (r["action"] != ACTION_REVIEW)]
        if st.button(f"Approve {len(clean)} clean recommendations", disabled=clean.empty,
                     help="Only lines with no exceptions, no conflicts and a calculable quantity."):
            errors = []
            for rid in clean["rec_id"]:
                try:
                    W.planner_approve(STORE, rid, ACTOR)
                except W.WorkflowError as e:
                    errors.append(str(e))
            st.session_state["flash"] = ("error", "; ".join(errors)) if errors else ("success", f"Approved {len(clean)} lines")
            st.rerun()

    st.subheader("Review a line")
    pick = st.selectbox("SKU", r["sku_id"] + " " + r["sku_name"], key="wb_pick").split(" ")[0]
    rec = r[r["sku_id"] == pick].iloc[0]
    st.markdown(rec["explanation"])
    if rec["conflicts"]:
        st.warning(" ".join(rec["conflicts"]))
    review_controls(rec, "wb")

    st.subheader("Exports")
    e1, e2 = st.columns(2)
    e1.download_button("Download recommendations (CSV)", to_csv_bytes(recommendations_frame(r)),
                       file_name=f"recommendations_{RUN_ID}.csv", mime="text/csv")
    if ACTOR.role == W.PROCUREMENT:
        n_ready = int((r["status"] == W.PROCUREMENT_APPROVED).sum())
        if e2.button(f"Create draft PO from {n_ready} approved lines", disabled=n_ready == 0):
            try:
                po = W.export_draft_po(STORE, RUN_ID, ACTOR)
                st.session_state["last_po"] = po
                st.session_state["flash"] = ("success", f"Draft PO {po['Draft_PO_ID'].iloc[0]} created ({len(po)} lines). Not submitted.")
            except W.WorkflowError as e:
                st.session_state["flash"] = ("error", str(e))
            st.rerun()
    else:
        e2.caption("Draft PO export: procurement role only.")
    if "last_po" in st.session_state:
        po = st.session_state["last_po"]
        st.markdown(f"**{po['Draft_PO_ID'].iloc[0]}**: {DRAFT_BANNER}")
        st.dataframe(po, hide_index=True, width="stretch")
        st.download_button("Download draft PO (CSV)", to_csv_bytes(po, DRAFT_BANNER),
                           file_name=f"{po['Draft_PO_ID'].iloc[0]}.csv", mime="text/csv")

    with st.expander("Audit log for this run"):
        ev = STORE.events(run_id=RUN_ID)
        st.dataframe(ev.drop(columns=["run_id"]), hide_index=True, width="stretch")
        st.download_button("Download audit log (CSV)", to_csv_bytes(ev), file_name=f"audit_{RUN_ID}.csv", mime="text/csv")


def page_quality():
    st.title("Data quality")
    issues = V.issues
    rows = []
    for name, fname in FILES.items():
        s = V.summaries.get(name)
        fi = issues[issues["file"] == fname] if not issues.empty else issues
        n_err = int((fi["severity"] == "error").sum()) if not fi.empty else 0
        n_warn = int((fi["severity"] == "warning").sum()) if not fi.empty else 0
        rows.append({
            "File": fname, "Status": "Missing" if s is None else ("Errors" if n_err else ("Warnings" if n_warn else "Valid")),
            "Rows": s["rows"] if s else 0, "Rows excluded": s.get("rows_excluded", 0) if s else 0,
            "Errors": n_err, "Warnings": n_warn, "Date range": s.get("date_range", "") if s else "",
            "Unique SKUs": str(s.get("unique_skus", "")) if s else "",
            "Unique distributors": str(s.get("unique_distributors", "")) if s else "",
            "Duplicate rows": s["duplicate_rows"] if s else 0, "SHA-256": V.hashes.get(fname, "")[:12],
        })
    st.dataframe(pd.DataFrame(rows).style.map(
        lambda s: {"Valid": "background-color:#DCEFE3", "Warnings": "background-color:#FCF0D9",
                   "Errors": "background-color:#F8DEDB", "Missing": "background-color:#F8DEDB"}.get(s, ""), subset=["Status"]),
        hide_index=True, width="stretch")

    st.subheader("Validation findings")
    sev = st.multiselect("Severity", ["error", "warning", "info"], default=["error", "warning", "info"])
    shown = issues[issues["severity"].isin(sev)] if not issues.empty else issues
    st.dataframe(shown, hide_index=True, width="stretch")
    st.download_button("Download validation findings (CSV)", to_csv_bytes(issues), file_name="validation_findings.csv", mime="text/csv")

    st.subheader("Inputs unavailable in the source data")
    st.markdown("""
- **Distributor-level sales**: weekly_sales.csv has no distributor column. Demand is analysed per SKU only.
- **Lead times, open purchase orders, in-transit stock**: not provided. Cover uses on-hand stock only.
- **Expiry dates / shelf life**: not provided. All on-hand stock is treated as usable.
- **Prices and costs**: not provided. Impact cannot be expressed in rupees.
- **Supplier per SKU**: not provided. Draft PO lines leave the supplier blank for procurement.
""")
    st.subheader("Data dictionary")
    st.dataframe(data_dictionary(V), hide_index=True, width="stretch")


def page_backtest():
    st.title("Backtesting and evaluation")
    horizon = st.segmented_control("Forecast horizon (weeks ahead)", [1, 2, 3, 4], default=1) or 1
    bt = load_backtest(HKEY, horizon)
    if bt.summary.empty:
        st.warning("Not enough history for a backtest.")
        return
    s = bt.summary.set_index("method")
    base, eng = s.at["baseline_12w", "WAPE"], s.at["rules_engine", "WAPE"]
    beats = eng < base
    with st.container(border=True):
        st.markdown(f"**Result:** the rules-engine demand estimate (12-week average + festival uplift) has WAPE "
                    f"**{eng:.1%}** vs **{base:.1%}** for the 12-week baseline over {int(s.at['rules_engine', 'observations'])} "
                    f"SKU-week forecasts. It **{'beats' if beats else 'does not beat'}** the baseline.")
        if not beats:
            st.markdown("In this sample, festival-month weeks did not rise by 25% for most SKUs, so the uplift overstates "
                        "demand. The festival rule should be reassessed with Raghav before a pilot. This tests forecast "
                        "accuracy only; it says nothing yet about rupee outcomes.")
    c = st.columns(3)
    for i, m in enumerate(["baseline_12w", "rules_engine", "recent_4w"]):
        c[i].metric(METHODS[m], f"WAPE {s.at[m, 'WAPE']:.1%}", help=f"MAE {s.at[m, 'MAE']:.1f} units, n={int(s.at[m, 'observations'])}")
    bw = bt.by_week.copy()
    bw["method"] = bw["method"].map(METHODS)
    fig = px.bar(bw, x="target", y="WAPE", color="method", barmode="group",
                 title="WAPE by target week (festival-month weeks from 2026-W40)",
                 color_discrete_sequence=["#18201B", AMBER, GREEN], labels={"target": "Target week", "method": ""})
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(chart_layout(fig), width="stretch")
    st.subheader("Method")
    for n in bt.notes:
        st.markdown(f"- {n}")
    n_obs = int(s["observations"].iloc[0])
    st.markdown(f"- Evaluated: {n_obs} SKU-week forecasts per method. Excluded origins: {len(bt.excluded)} "
                f"(fewer than {CFG.baseline_weeks} weeks of history, or gaps).")
    st.markdown("- MAE = mean absolute error in units. WAPE = sum of absolute errors / sum of actual units.")
    with st.expander("Per-SKU WAPE"):
        per = bt.predictions.groupby(["sku_id", "method"]).apply(
            lambda g: g["abs_error"].sum() / g["actual"].sum(), include_groups=False).unstack("method")
        st.dataframe(per.style.format("{:.1%}"), width="stretch")
    with st.expander("All predictions"):
        st.dataframe(bt.predictions, hide_index=True, width="stretch")
    with st.expander("Excluded records"):
        st.dataframe(bt.excluded, hide_index=True, width="stretch")
    st.caption("Business outcomes (stockouts, write-offs) are not simulated: there is no historical inventory, lead-time "
               "or price data. A lower simulated risk would not prove savings in any case.")




def page_ops():
    st.title("Operations intelligence")
    st.caption("Option C. Signals are checked as each week lands. Priya triages them; procurement must acknowledge an "
               "open signal before any PO line for that SKU can be approved.")
    show_flash()
    if not require_run():
        return
    st.subheader("Weekly operations pulse")
    st.dataframe(OI.weekly_pulse(A), hide_index=True, width="stretch")
    with st.expander("Coverage of the 12-metric report from the available data"):
        st.dataframe(pd.DataFrame(OI.METRIC_CATALOG, columns=["Metric", "Availability", "Note"]),
                     hide_index=True, width="stretch")

    sig = STORE.signals(RUN_ID)
    st.subheader(f"Open signals for this run (latest week {A.anchor_week})")
    st.caption(f"Proposed thresholds (assumptions): drop of more than {OI.DROP_VS_PRIOR4:.0%} vs the previous 4-week "
               f"average or more than {OI.DROP_WOW:.0%} week on week; spike of more than {OI.SPIKE_VS_PRIOR4:.0%}.")
    if sig.empty:
        st.success(f"No SKU crossed a signal threshold in {A.anchor_week}. No PO line is held by Option C in this run.")
    else:
        c = st.columns(4)
        for i, s in enumerate(OI.SIGNAL_STATUSES):
            c[i].metric(s, int((sig["status"] == s).sum()))
        for _, s in sig.iterrows():
            with st.expander(f"{s['sku_id']} | {s['signal_type']} | {s['status']}", expanded=s["status"] in OI.SIGNAL_OPEN):
                st.markdown(f"{s['message']} (week {s['week']}, severity {s['severity']})")
                if s["status"] == OI.SIGNAL_NEW:
                    if ACTOR.role != W.ANALYST:
                        st.info("Waiting for Priya (analyst) to triage.")
                    else:
                        with st.form(f"tri_{s['sid']}"):
                            note = st.text_input("Note (required to dismiss)")
                            b1, b2 = st.columns(2)
                            if b1.form_submit_button("Surface to procurement", type="primary"):
                                run_action(lambda: W.analyst_surface(STORE, s["sid"], ACTOR, note), "Signal surfaced")
                            if b2.form_submit_button("Dismiss"):
                                run_action(lambda: W.analyst_dismiss(STORE, s["sid"], ACTOR, note), "Signal dismissed")
                elif s["status"] == OI.SIGNAL_SURFACED:
                    if ACTOR.role != W.PROCUREMENT:
                        st.info("Waiting for procurement to acknowledge.")
                    else:
                        with st.form(f"ack_{s['sid']}"):
                            dec = st.radio("Decision", W.SIGNAL_DECISIONS, horizontal=True)
                            note = st.text_input("Note (required)")
                            if st.form_submit_button("Acknowledge", type="primary"):
                                run_action(lambda: W.procurement_acknowledge(STORE, s["sid"], ACTOR, dec, note),
                                           "Signal acknowledged")
                else:
                    st.caption(f"{s['status']}: {s.get('decision') or ''} {s.get('note') or ''}")

    st.subheader("Signal history (all weeks, detection only)")
    hist = OI.scan_signals(A.weekly)
    if hist.empty:
        st.caption("No signals in the history at the current thresholds.")
    else:
        st.caption(f"{len(hist)} signals across {hist['week'].nunique()} weeks. Earlier weeks are shown to demonstrate "
                   "detection; only the latest week is routed for action.")
        show = hist.assign(change=lambda d: (d["change_pct"] * 100).round(1))[
            ["week", "sku_id", "signal_type", "latest_units", "reference_units", "change", "severity", "message"]]
        st.dataframe(show, hide_index=True, width="stretch",
                     column_config={"change": st.column_config.NumberColumn("Change %", format="%+.1f%%"),
                                    "reference_units": st.column_config.NumberColumn("Reference", format="%.1f")})
        fig = px.scatter(hist, x="week", y="sku_id", color="signal_type", size=hist["change_pct"].abs(),
                         title="Signals by week and SKU", color_discrete_map={"DROP_VS_TREND": RED,
                         "DROP_WEEK_ON_WEEK": AMBER, "SPIKE_VS_TREND": BLUE})
        st.plotly_chart(chart_layout(fig, 360), width="stretch")


def page_plan():
    st.title("Plan")
    st.subheader("ROI scenarios (assumptions)")
    st.dataframe(RD.roi_scenarios(), hide_index=True, width="stretch")
    st.caption("Reported loss Rs 28-34L/quarter from the case. Reduction percentages are assumptions. The Rs 15L budget is "
               "treated as a one-time cost. No savings have been realised or measured.")

    st.subheader("90-day implementation plan (proposed)")
    plan = RD.plan_frame()
    start = pd.Timestamp(A.analysis_date or "2026-10-19")
    plan["Start"] = plan["Start day"].map(lambda d: start + pd.Timedelta(days=d - 1))
    plan["End"] = plan["End day"].map(lambda d: start + pd.Timedelta(days=d))
    fig = px.timeline(plan, x_start="Start", x_end="End", y="Phase", hover_data=["Work"], color_discrete_sequence=[GREEN])
    fig.update_yaxes(autorange="reversed", title=None)
    st.plotly_chart(chart_layout(fig, 300), width="stretch")
    st.dataframe(plan[["Start day", "End day", "Phase", "Work"]], hide_index=True, width="stretch")
    st.caption("Dates are illustrative from the analysis date and will move with data access and quality.")

    st.subheader("Prototype assumptions: rule priority")
    for t, d in PRIORITY_STEPS:
        st.markdown(f"- **{t}**: {d}")
    st.subheader("Unresolved business questions")
    for q in RD.OPEN_QUESTIONS:
        st.markdown(f"- {q}")


pages = [
    st.Page(page_overview, title="Executive overview", url_path="overview", default=True),
    st.Page(page_demand, title="Demand planning", url_path="demand"),
    st.Page(page_exceptions, title="Exception review", url_path="exceptions"),
    st.Page(page_workbench, title="Replenishment workbench", url_path="workbench"),
    st.Page(page_ops, title="Operations intelligence", url_path="ops-intelligence"),
    st.Page(page_quality, title="Data quality", url_path="data-quality"),
    st.Page(page_backtest, title="Backtesting", url_path="backtest"),
    st.Page(page_plan, title="Plan", url_path="plan"),
]
st.navigation(pages).run()
