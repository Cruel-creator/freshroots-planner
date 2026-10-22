import ast
import re
from pathlib import Path

import pandas as pd
import pytest
from conftest import LABELS, flat, run_sku

from freshroots import ops_intel as OI
from freshroots import workflow as W
from freshroots.engine import ACTION_REORDER_HIGH, ACTION_REVIEW, Analysis
from freshroots.ops_intel import SIGNAL_COLUMNS
from freshroots.store import Store

PLANNER = W.Actor("Raghav Kulkarni", W.PLANNER)
PROC = W.Actor("Procurement Officer", W.PROCUREMENT)
ANALYST = W.Actor("Priya Sharma", W.ANALYST)


def make_rec(cfg, sku, **kw):
    r = run_sku(cfg, **kw)
    r.update({"sku_id": sku, "sku_name": f"Name {sku}", "category": "Snack", "perishability": "Low",
              "is_perishable": kw.get("perishable", False), "unit": "Units", "mapped_distributor_id": "D1",
              "mapped_distributor": "D1 Test", "scope": "SKU-level", "inventory_as_of": "2026-10-19",
              "weeks_of_history": 12, "planning_month": "2026-10", "exception_codes": []})
    return r


@pytest.fixture
def setup(cfg):
    recs = pd.DataFrame([
        make_rec(cfg, "A_STOCKOUT", stock=200.0),                    # reorder now, qty 100
        make_rec(cfg, "B_OVERSTOCK", stock=5000.0),                  # pause
        make_rec(cfg, "C_CONFLICT", units={w: 90.0 if i < 8 else 130.0 for i, w in enumerate(LABELS)}, stock=5000.0),
        make_rec(cfg, "D_NOQTY", stock=100.0, std=None),             # reorder, quantity unknown
        make_rec(cfg, "E_SIGNAL", stock=200.0),                      # reorder, has an open signal
    ])
    a = Analysis(recs, pd.DataFrame(), pd.DataFrame(), "2026-10-19", "2026-W42", LABELS, "2026-10", True)
    sig = pd.DataFrame([{"signal_id": "E_SIGNAL:2026-W42:DROP_VS_TREND", "sku_id": "E_SIGNAL", "week": "2026-W42",
                         "signal_type": "DROP_VS_TREND", "latest_units": 60.0, "reference_units": 100.0,
                         "change_pct": -0.4, "severity": "high", "message": "60 vs 100", "is_latest_week": True}],
                       columns=SIGNAL_COLUMNS)
    store = Store(":memory:")
    run_id = W.create_run(store, a, cfg, {"f.csv": "abc"}, W.Actor("test", W.SYSTEM), signals=sig)
    return store, run_id


def rid(run_id, sku):
    return f"{run_id}:{sku}"


def test_run_starts_pending_planner_with_audit_trail(setup):
    store, run_id = setup
    recs = store.recs(run_id)
    assert set(recs["status"]) == {W.PENDING_PLANNER}
    ev = store.events(run_id=run_id)
    assert (ev["event_type"] == "generated").sum() == 5
    assert (ev["to_status"] == W.GENERATED).sum() == 5
    assert ev["ts"].notna().all() and ev["actor"].notna().all()


def test_planner_approve_routes_reorder_to_procurement(setup):
    store, run_id = setup
    W.planner_approve(store, rid(run_id, "A_STOCKOUT"), PLANNER)
    rec = store.rec(rid(run_id, "A_STOCKOUT"))
    assert rec["status"] == W.PENDING_PROCUREMENT
    assert rec["planner_decision"] == "approved"
    ev = store.events(rec_id=rid(run_id, "A_STOCKOUT"))
    assert {"planner_approved", "sent_to_procurement"} <= set(ev["event_type"])
    assert (ev.loc[ev["event_type"] == "planner_approved", "actor"] == "Raghav Kulkarni").all()


def test_pause_approval_does_not_reach_procurement(setup):
    store, run_id = setup
    W.planner_approve(store, rid(run_id, "B_OVERSTOCK"), PLANNER)
    assert store.rec(rid(run_id, "B_OVERSTOCK"))["status"] == W.PLANNER_APPROVED


def test_conflict_cannot_be_plain_approved(setup):
    store, run_id = setup
    assert store.rec(rid(run_id, "C_CONFLICT"))["action"] == ACTION_REVIEW
    with pytest.raises(W.ApprovalBlocked):
        W.planner_approve(store, rid(run_id, "C_CONFLICT"), PLANNER)


def test_missing_quantity_blocks_approval(setup):
    store, run_id = setup
    with pytest.raises(W.ApprovalBlocked):
        W.planner_approve(store, rid(run_id, "D_NOQTY"), PLANNER)


def test_override_requires_reason(setup):
    store, run_id = setup
    for bad in ("", "   ", "too short"):
        with pytest.raises(W.ApprovalBlocked):
            W.planner_override(store, rid(run_id, "C_CONFLICT"), PLANNER, action=ACTION_REORDER_HIGH, qty=80, reason=bad)
    assert store.rec(rid(run_id, "C_CONFLICT"))["status"] == W.PENDING_PLANNER


def test_override_with_reason_is_logged(setup):
    store, run_id = setup
    reason = "Scheme ends this week; order a reduced quantity"
    W.planner_override(store, rid(run_id, "C_CONFLICT"), PLANNER, action=ACTION_REORDER_HIGH, qty=80, reason=reason)
    rec = store.rec(rid(run_id, "C_CONFLICT"))
    assert rec["status"] == W.PENDING_PROCUREMENT
    assert rec["final_qty"] == 80 and rec["planner_reason"] == reason
    ev = store.events(rec_id=rid(run_id, "C_CONFLICT"))
    row = ev[ev["event_type"] == "planner_overridden"].iloc[0]
    assert row["reason"] == reason and row["role"] == W.PLANNER and row["to_status"] == W.PLANNER_OVERRIDDEN


def test_override_reorder_needs_positive_quantity(setup):
    store, run_id = setup
    with pytest.raises(W.ApprovalBlocked):
        W.planner_override(store, rid(run_id, "D_NOQTY"), PLANNER, action=ACTION_REORDER_HIGH, qty=0,
                           reason="Planner sets the quantity manually")


def test_roles_are_enforced(setup):
    store, run_id = setup
    with pytest.raises(W.PermissionDenied):
        W.planner_approve(store, rid(run_id, "A_STOCKOUT"), PROC)
    W.planner_approve(store, rid(run_id, "A_STOCKOUT"), PLANNER)
    with pytest.raises(W.PermissionDenied):
        W.procurement_approve(store, rid(run_id, "A_STOCKOUT"), PLANNER)


def test_procurement_cannot_skip_planner(setup):
    store, run_id = setup
    with pytest.raises(W.WorkflowError):
        W.procurement_approve(store, rid(run_id, "A_STOCKOUT"), PROC)


def test_reject_requires_reason(setup):
    store, run_id = setup
    with pytest.raises(W.ApprovalBlocked):
        W.reject(store, rid(run_id, "A_STOCKOUT"), PLANNER, "no")
    W.reject(store, rid(run_id, "A_STOCKOUT"), PLANNER, "Stock transfer from Goa covers this")
    assert store.rec(rid(run_id, "A_STOCKOUT"))["status"] == W.REJECTED


def test_open_signal_blocks_procurement_until_acknowledged(setup):
    store, run_id = setup
    W.planner_approve(store, rid(run_id, "E_SIGNAL"), PLANNER)
    with pytest.raises(W.ApprovalBlocked):
        W.procurement_approve(store, rid(run_id, "E_SIGNAL"), PROC)
    sid = store.signals(run_id)["sid"].iloc[0]
    with pytest.raises(W.PermissionDenied):
        W.analyst_surface(store, sid, PROC)
    W.analyst_surface(store, sid, ANALYST, "Distributor cut orders after competitor scheme")
    with pytest.raises(W.ApprovalBlocked):                       # surfaced but not yet acknowledged
        W.procurement_approve(store, rid(run_id, "E_SIGNAL"), PROC)
    with pytest.raises(W.ApprovalBlocked):
        W.procurement_acknowledge(store, sid, PROC, "Proceed as planned", "ok")   # note too short
    W.procurement_acknowledge(store, sid, PROC, "Proceed as planned", "Checked with sales: one-off dip")
    W.procurement_approve(store, rid(run_id, "E_SIGNAL"), PROC)
    assert store.rec(rid(run_id, "E_SIGNAL"))["status"] == W.PROCUREMENT_APPROVED
    assert store.signal(sid)["status"] == OI.SIGNAL_ACKNOWLEDGED


def test_dismissing_a_signal_requires_reason(setup):
    store, run_id = setup
    sid = store.signals(run_id)["sid"].iloc[0]
    with pytest.raises(W.ApprovalBlocked):
        W.analyst_dismiss(store, sid, ANALYST, "")
    W.analyst_dismiss(store, sid, ANALYST, "Data entry correction, not real demand")
    assert W.open_signals_for(store, run_id, "E_SIGNAL").empty


def test_draft_po_generation(setup):
    store, run_id = setup
    with pytest.raises(W.ApprovalBlocked):
        W.export_draft_po(store, run_id, PROC)                  # nothing approved yet
    W.planner_approve(store, rid(run_id, "A_STOCKOUT"), PLANNER)
    W.procurement_approve(store, rid(run_id, "A_STOCKOUT"), PROC)
    with pytest.raises(W.PermissionDenied):
        W.export_draft_po(store, run_id, PLANNER)
    po = W.export_draft_po(store, run_id, PROC)
    assert len(po) == 1
    assert po["Status"].iloc[0] == "DRAFT - NOT SUBMITTED"
    assert po["Quantity"].iloc[0] == 100
    assert po["Supplier"].iloc[0].startswith("NOT IN SOURCE DATA")
    assert store.rec(rid(run_id, "A_STOCKOUT"))["status"] == W.EXPORTED_DRAFT


def test_external_order_placement_is_impossible():
    with pytest.raises(W.ExternalSubmissionDisabled):
        W.ExternalOrderGateway().submit_purchase_order({"sku": "X", "qty": 1})


def test_no_network_libraries_in_the_package():
    """Only the optional Gemini explainer (llm.py) may reach the network, and only Google's API."""
    banned = {"requests", "urllib", "http", "httpx", "aiohttp", "socket", "smtplib", "ftplib"}
    pkg = Path(__file__).resolve().parent.parent / "freshroots"
    llm_src = (pkg / "llm.py").read_text(encoding="utf-8")
    assert set(re.findall(r"https?://([^/\"']+)", llm_src)) == {"generativelanguage.googleapis.com"}
    for py in pkg.glob("*.py"):
        if py.name == "llm.py":
            continue
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            assert not banned.intersection(names), f"{py.name} imports {names}"


def test_recommendations_are_reproducible(cfg):
    a = run_sku(cfg, units=flat(100), stock=500.0)
    b = run_sku(cfg, units=flat(100), stock=500.0)
    assert a == b
