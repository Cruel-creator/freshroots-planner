"""Human approval workflow and control boundaries.

Raghav (planner) reviews every recommendation; procurement approves every
purchase-order line. Nothing is ever sent to SAP, Zoho or any external system.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import ops_intel
from .config import RULE_VERSION, Config
from .engine import ACTION_REVIEW, ALL_ACTIONS, REORDER_ACTIONS, Analysis
from .store import Store

GENERATED = "Generated"
PENDING_PLANNER = "Pending planner review"
PLANNER_APPROVED = "Planner approved"
PLANNER_OVERRIDDEN = "Planner overridden"
PENDING_PROCUREMENT = "Pending procurement approval"
PROCUREMENT_APPROVED = "Procurement approved"
REJECTED = "Rejected"
EXPORTED_DRAFT = "Exported as draft"
STATUSES = [GENERATED, PENDING_PLANNER, PLANNER_APPROVED, PLANNER_OVERRIDDEN, PENDING_PROCUREMENT,
            PROCUREMENT_APPROVED, REJECTED, EXPORTED_DRAFT]

PLANNER = "planner"
PROCUREMENT = "procurement"
ANALYST = "analyst"
VIEWER = "viewer"
SYSTEM = "system"

MIN_REASON_LENGTH = 10

SIGNAL_DECISIONS = ["Hold related orders", "Proceed as planned"]


@dataclass(frozen=True)
class Actor:
    name: str
    role: str


DEFAULT_ACTORS = [
    Actor("Raghav Kulkarni", PLANNER),
    Actor("Procurement Officer", PROCUREMENT),
    Actor("Priya Sharma", ANALYST),
    Actor("Deepa Nair", VIEWER),
]


class WorkflowError(Exception):
    pass


class PermissionDenied(WorkflowError):
    pass


class ApprovalBlocked(WorkflowError):
    pass


class ExternalSubmissionDisabled(WorkflowError):
    pass


class ExternalOrderGateway:
    """The only place an order could leave the prototype. It always refuses."""

    def submit_purchase_order(self, *_args, **_kwargs):
        raise ExternalSubmissionDisabled(
            "This prototype never places or submits purchase orders. Export a draft and enter it in Zoho manually.")


def _require_role(actor: Actor, role: str) -> None:
    if actor.role != role:
        raise PermissionDenied(f"{actor.name} ({actor.role}) cannot perform a {role} action.")


def _require_reason(reason: str | None) -> str:
    r = (reason or "").strip()
    if len(r) < MIN_REASON_LENGTH:
        raise ApprovalBlocked(f"A reason of at least {MIN_REASON_LENGTH} characters is required.")
    return r


def _get(store: Store, rec_id: str, expected: str) -> dict:
    rec = store.rec(rec_id)
    if rec is None:
        raise WorkflowError(f"Unknown recommendation {rec_id}.")
    if rec["status"] != expected:
        raise WorkflowError(f"{rec['sku_id']} is '{rec['status']}', expected '{expected}'.")
    return rec


def create_run(store: Store, analysis: Analysis, cfg: Config, input_hashes: dict, actor: Actor,
               signals: pd.DataFrame | None = None) -> str:
    """Store recommendations (Option A) and open signals from the latest week (Option C)."""
    run_id = store.create_run(
        analysis.recommendations, actor=actor.name, role=actor.role, rule_version=RULE_VERSION,
        rule_params=cfg.rule_params(), input_hashes=input_hashes, analysis_date=analysis.analysis_date,
        anchor_week=analysis.anchor_week, initial_status=GENERATED, routed_status=PENDING_PLANNER)
    if signals is None:
        signals = ops_intel.scan_signals(analysis.weekly)
        signals = signals[signals["is_latest_week"]]
    if not signals.empty:
        store.add_signals(run_id, signals, actor=actor.name, role=actor.role, status=ops_intel.SIGNAL_NEW)
    return run_id


def open_signals_for(store: Store, run_id: str, sku_id: str) -> pd.DataFrame:
    sig = store.signals(run_id)
    if sig.empty:
        return sig
    return sig[(sig["sku_id"] == sku_id) & (sig["status"].isin(ops_intel.SIGNAL_OPEN))]


def analyst_surface(store: Store, sid: str, actor: Actor, note: str | None = None) -> None:
    _require_role(actor, ANALYST)
    store.transition_signal(sid, actor=actor.name, role=actor.role, event_type="signal_surfaced",
                            from_status=ops_intel.SIGNAL_NEW, to_status=ops_intel.SIGNAL_SURFACED,
                            reason=(note or "").strip() or None, note=(note or "").strip() or None)


def analyst_dismiss(store: Store, sid: str, actor: Actor, reason: str) -> None:
    _require_role(actor, ANALYST)
    reason = _require_reason(reason)
    store.transition_signal(sid, actor=actor.name, role=actor.role, event_type="signal_dismissed",
                            from_status=ops_intel.SIGNAL_NEW, to_status=ops_intel.SIGNAL_DISMISSED,
                            reason=reason, note=reason)


def procurement_acknowledge(store: Store, sid: str, actor: Actor, decision: str, note: str) -> None:
    _require_role(actor, PROCUREMENT)
    if decision not in SIGNAL_DECISIONS:
        raise ApprovalBlocked(f"Decision must be one of: {', '.join(SIGNAL_DECISIONS)}.")
    note = _require_reason(note)
    store.transition_signal(sid, actor=actor.name, role=actor.role, event_type="signal_acknowledged",
                            from_status=ops_intel.SIGNAL_SURFACED, to_status=ops_intel.SIGNAL_ACKNOWLEDGED,
                            reason=note, decision=decision, note=note)


def _after_planner(store: Store, rec_id: str, actor: Actor, status: str, final_action: str, final_qty) -> None:
    if final_action in REORDER_ACTIONS and final_qty:
        store.transition(rec_id, actor=actor.name, role=actor.role, event_type="sent_to_procurement",
                         from_status=status, to_status=PENDING_PROCUREMENT)


def planner_approve(store: Store, rec_id: str, actor: Actor) -> None:
    _require_role(actor, PLANNER)
    rec = _get(store, rec_id, PENDING_PLANNER)
    action, qty = rec["action"], rec["recommended_qty"]
    if action not in ALL_ACTIONS or action == ACTION_REVIEW:
        raise ApprovalBlocked("This recommendation has no single rule-based answer. Use override to set the action, "
                              "quantity and reason.")
    if action in REORDER_ACTIONS and (qty is None or qty <= 0):
        raise ApprovalBlocked("Quantity is missing. Use override to enter a quantity and reason.")
    store.transition(rec_id, actor=actor.name, role=actor.role, event_type="planner_approved",
                     from_status=PENDING_PLANNER, to_status=PLANNER_APPROVED,
                     planner_decision="approved", final_action=action, final_qty=qty)
    _after_planner(store, rec_id, actor, PLANNER_APPROVED, action, qty)


def planner_override(store: Store, rec_id: str, actor: Actor, *, action: str, qty: float | None, reason: str) -> None:
    _require_role(actor, PLANNER)
    rec = _get(store, rec_id, PENDING_PLANNER)
    reason = _require_reason(reason)
    if action not in ALL_ACTIONS or action == ACTION_REVIEW:
        raise ApprovalBlocked("Choose a concrete action (reorder, pause or no action).")
    if action in REORDER_ACTIONS:
        if qty is None or qty <= 0:
            raise ApprovalBlocked("A reorder override needs a positive quantity.")
    else:
        qty = 0.0
    store.transition(rec_id, actor=actor.name, role=actor.role, event_type="planner_overridden",
                     from_status=PENDING_PLANNER, to_status=PLANNER_OVERRIDDEN, reason=reason,
                     details={"from_action": rec["action"], "from_qty": rec["recommended_qty"],
                              "to_action": action, "to_qty": qty},
                     planner_decision="overridden", planner_reason=reason, final_action=action, final_qty=qty)
    _after_planner(store, rec_id, actor, PLANNER_OVERRIDDEN, action, qty)


def reject(store: Store, rec_id: str, actor: Actor, reason: str) -> None:
    rec = store.rec(rec_id)
    if rec is None:
        raise WorkflowError(f"Unknown recommendation {rec_id}.")
    if rec["status"] == PENDING_PLANNER:
        _require_role(actor, PLANNER)
    elif rec["status"] == PENDING_PROCUREMENT:
        _require_role(actor, PROCUREMENT)
    else:
        raise WorkflowError(f"Cannot reject a recommendation in status '{rec['status']}'.")
    reason = _require_reason(reason)
    store.transition(rec_id, actor=actor.name, role=actor.role, event_type="rejected",
                     from_status=rec["status"], to_status=REJECTED, reason=reason)


def procurement_approve(store: Store, rec_id: str, actor: Actor) -> None:
    _require_role(actor, PROCUREMENT)
    rec = _get(store, rec_id, PENDING_PROCUREMENT)
    if rec["final_action"] not in REORDER_ACTIONS or not rec["final_qty"] or rec["final_qty"] <= 0:
        raise ApprovalBlocked("Only reorder lines with a positive quantity can be approved.")
    open_sig = open_signals_for(store, rec["run_id"], rec["sku_id"])
    if not open_sig.empty:
        raise ApprovalBlocked(f"{rec['sku_id']} has {len(open_sig)} open operations signal(s) "
                              f"({', '.join(open_sig['signal_type'])}). Priya must triage and procurement must "
                              "acknowledge them before this PO line can be approved.")
    store.transition(rec_id, actor=actor.name, role=actor.role, event_type="procurement_approved",
                     from_status=PENDING_PROCUREMENT, to_status=PROCUREMENT_APPROVED)


def export_draft_po(store: Store, run_id: str, actor: Actor) -> pd.DataFrame:
    """Draft PO lines for procurement-approved items; marks them 'Exported as draft'. Submits nothing."""
    _require_role(actor, PROCUREMENT)
    recs = store.recs(run_id)
    approved = recs[recs["status"] == PROCUREMENT_APPROVED] if not recs.empty else recs
    if approved.empty:
        raise ApprovalBlocked("No procurement-approved lines to export.")
    from .exports import draft_po_frame
    po = draft_po_frame(approved, run_id, actor.name)
    for rec_id in approved["rec_id"]:
        store.transition(rec_id, actor=actor.name, role=actor.role, event_type="exported_as_draft",
                         from_status=PROCUREMENT_APPROVED, to_status=EXPORTED_DRAFT,
                         details={"draft_po_id": po["Draft_PO_ID"].iloc[0]})
    return po
