"""JSON API over the engine, workflow and store. Serves the built web UI from web/dist.

Run: python serve.py   (http://127.0.0.1:8000)
"""
from __future__ import annotations

import json
import math
from datetime import date, datetime

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import ops_intel as OI
from . import readiness as RD
from . import workflow as W
from .backtest import METHODS, run_backtest
from .config import PROJECT_ROOT, RULE_VERSION, database_target, load_config
from .engine import ACTION_REVIEW, ALL_ACTIONS, PRIORITY_STEPS, REORDER_ACTIONS, analyse
from .exports import DRAFT_BANNER, recommendations_frame, to_csv_bytes
from .ingest import FILES, data_dictionary, file_sha256, validate
from .llm import attach_ai_notes, get_explainer
from .rules import FLAG_LABELS
from .store import Store

CFG = load_config()
STORE = Store(database_target(CFG))
WEB_DIST = PROJECT_ROOT / "web" / "dist"

app = FastAPI(title="Freshroots demand planning", docs_url="/api/docs", openapi_url="/api/openapi.json")

_cache: dict = {}


def clean(o):
    """Recursively make engine output JSON-safe. NaN and inf become null (callers flag infinity)."""
    if isinstance(o, pd.DataFrame):
        return [clean(r) for r in o.to_dict(orient="records")]
    if isinstance(o, pd.Series):
        return [clean(v) for v in o.tolist()]
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set)):
        return [clean(v) for v in o]
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, (np.floating, float)):
        f = float(o)
        return None if math.isnan(f) or math.isinf(f) else f
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, (pd.Timestamp, datetime)):
        return str(o)
    if isinstance(o, date):
        return o.isoformat()
    if o is pd.NA or o is pd.NaT:
        return None
    return o


def input_hashes() -> dict:
    return {f: file_sha256(CFG.data_dir / f) for f in FILES.values() if (CFG.data_dir / f).exists()}


def current():
    hashes = input_hashes()
    key = tuple(sorted(hashes.items()))
    if _cache.get("key") != key:
        v = validate(CFG.data_dir)
        a = analyse(v, CFG)
        _cache.clear()
        _cache.update(key=key, v=v, a=a, hashes=hashes, bt={})
    return _cache["v"], _cache["a"], _cache["hashes"]


def backtest(h: int):
    _, a, _ = current()
    if h not in _cache["bt"]:
        _cache["bt"][h] = run_backtest(a.weekly, CFG, horizon=h)
    return _cache["bt"][h]


def actor_by_name(name: str) -> W.Actor:
    for a in W.DEFAULT_ACTORS:
        if a.name == name:
            return a
    raise HTTPException(400, f"Unknown actor '{name}'.")


def ensure_run() -> str:
    run_id = STORE.latest_run_id()
    if run_id is None:
        _, a, hashes = current()
        run_id = W.create_run(STORE, a, CFG, hashes, W.Actor("system (first launch)", W.SYSTEM))
    return run_id


def checkpoints(r: dict) -> list[str]:
    pts = ["Raghav reviews the exception" if r.get("needs_review") else "Raghav signs off"]
    if r.get("final_action") in REORDER_ACTIONS or r.get("action") in REORDER_ACTIONS or r.get("action") == ACTION_REVIEW:
        pts.append("Procurement approves the PO line")
    return pts


def recs_payload(run_id: str) -> list[dict]:
    out = []
    for r in STORE.recs(run_id).to_dict(orient="records"):
        cover = r.get("weeks_of_cover")
        r["cover_is_infinite"] = isinstance(cover, float) and math.isinf(cover)
        r["needs_review"] = bool(r.get("needs_review"))
        r["checkpoints"] = checkpoints(r)
        out.append(clean(r))
    return out


def handle(fn):
    try:
        fn()
    except W.PermissionDenied as e:
        raise HTTPException(403, str(e))
    except (W.WorkflowError, RuntimeError) as e:
        raise HTTPException(409, str(e))
    return {"ok": True}


def backtest_payload(bt) -> dict:
    per = pd.DataFrame()
    if not bt.predictions.empty:
        per = (bt.predictions.groupby(["sku_id", "method"])
               .apply(lambda g: g["abs_error"].sum() / g["actual"].sum(), include_groups=False)
               .unstack("method").reset_index())
    return {"summary": bt.summary, "by_week": bt.by_week, "per_sku": per, "methods": METHODS,
            "notes": bt.notes, "excluded": len(bt.excluded), "observations": len(bt.predictions)}


# ------------------------------------------------------------------ reads --
@app.get("/api/state")
def state(run_id: str | None = None):
    v, a, hashes = current()
    latest = ensure_run()
    run_id = run_id or latest
    run = STORE.run(run_id)
    if run is None:
        raise HTTPException(404, f"Unknown run {run_id}")
    bt = backtest(1)
    weekly = a.weekly[["SKU_ID", "week", "week_start", "units", "month", "is_festival"]].copy()
    return JSONResponse(clean({
        "meta": {
            "analysis_date": a.analysis_date, "anchor_week": a.anchor_week, "window": a.window_labels,
            "planning_month": a.planning_month, "planning_month_festival": a.planning_month_festival,
            "rule_version": RULE_VERSION, "run": run, "runs": STORE.runs()[["run_id", "created_at", "created_by"]],
            "inputs_changed": json.loads(run["input_hashes_json"]) != hashes,
            "thresholds": {"stockout": CFG.stockout_weeks, "overstock": CFG.overstock_weeks,
                           "perishable_min": CFG.perishable_min_weeks, "perishable_max": CFG.perishable_max_weeks,
                           "high_demand": CFG.high_demand_threshold, "uplift": CFG.festival_uplift,
                           "signal_drop": OI.DROP_VS_PRIOR4, "signal_wow": OI.DROP_WOW,
                           "signal_spike": OI.SPIKE_VS_PRIOR4},
            "flag_labels": FLAG_LABELS, "actions": ALL_ACTIONS, "review_action": ACTION_REVIEW,
            "reorder_actions": sorted(REORDER_ACTIONS), "statuses": W.STATUSES,
            "signal_statuses": OI.SIGNAL_STATUSES, "signal_decisions": W.SIGNAL_DECISIONS,
            "actors": [{"name": x.name, "role": x.role} for x in W.DEFAULT_ACTORS],
            "min_reason": W.MIN_REASON_LENGTH, "llm_provider": CFG.llm_provider,
        },
        "recommendations": recs_payload(run_id),
        "exceptions": a.exceptions,
        "weekly": weekly,
        "signals": STORE.signals(run_id),
        "signal_history": OI.scan_signals(a.weekly),
        "pulse": OI.weekly_pulse(a),
        "metric_catalog": [dict(zip(["metric", "availability", "note"], m)) for m in OI.METRIC_CATALOG],
        "quality": {
            "summaries": v.summaries, "issues": v.issues, "errors": v.error_count, "warnings": v.warning_count,
            "dictionary": data_dictionary(v), "hashes": v.hashes,
        },
        "backtest": backtest_payload(bt),
        "readiness": {
            "roi": RD.roi_scenarios(), "plan": RD.plan_frame(), "open_questions": RD.OPEN_QUESTIONS,
            "priority_steps": [dict(zip(["step", "rule"], p)) for p in PRIORITY_STEPS],
        },
    }))


@app.get("/api/backtest")
def backtest_h(h: int = 1):
    if h not in (1, 2, 3, 4):
        raise HTTPException(400, "Horizon must be 1-4 weeks.")
    return JSONResponse(clean(backtest_payload(backtest(h))))


@app.get("/api/ai-notes")
def ai_notes():
    """Optional Gemini notes on exceptions. Computed once per data version; never changes a recommendation."""
    _, a, _ = current()
    explainer = get_explainer(CFG.llm_provider)
    if not explainer.enabled:
        return {"enabled": False, "provider": explainer.name, "notes": []}
    if "ai" not in _cache:
        notes = attach_ai_notes(a.exceptions, explainer)
        if "ai_note" in notes:
            notes = notes[notes["ai_note"].notna()]
        found = [{"sku_id": r["sku_id"], "code": r["code"], "note": r["ai_note"], "category": r["ai_review_category"]}
                 for r in (notes.to_dict(orient="records") if "ai_note" in notes else [])]
        if found or a.exceptions.empty:
            _cache["ai"] = found  # failures are not cached, so a fixed key works without a redeploy
        else:
            return {"enabled": True, "provider": explainer.name, "notes": [],
                    "error": "Gemini did not answer. Check that GEMINI_API_KEY is a valid Google AI Studio key."}
    return {"enabled": True, "provider": explainer.name, "model": getattr(explainer, "model", None), "notes": _cache["ai"]}


@app.get("/api/events")
def events(run_id: str):
    return JSONResponse(clean(STORE.events(run_id=run_id)))


# ----------------------------------------------------------------- writes --
class ActorBody(BaseModel):
    actor: str


class OverrideBody(ActorBody):
    action: str
    qty: float | None = None
    reason: str = ""


class ReasonBody(ActorBody):
    reason: str = ""


class AckBody(ActorBody):
    decision: str
    note: str = ""


@app.post("/api/runs")
def create_run(body: ActorBody):
    _, a, hashes = current()
    return {"run_id": W.create_run(STORE, a, CFG, hashes, actor_by_name(body.actor))}


@app.post("/api/recs/{rec_id}/approve")
def approve(rec_id: str, body: ActorBody):
    return handle(lambda: W.planner_approve(STORE, rec_id, actor_by_name(body.actor)))


@app.post("/api/recs/{rec_id}/override")
def override(rec_id: str, body: OverrideBody):
    return handle(lambda: W.planner_override(STORE, rec_id, actor_by_name(body.actor),
                                             action=body.action, qty=body.qty, reason=body.reason))


@app.post("/api/recs/{rec_id}/reject")
def reject(rec_id: str, body: ReasonBody):
    return handle(lambda: W.reject(STORE, rec_id, actor_by_name(body.actor), body.reason))


@app.post("/api/recs/{rec_id}/procure")
def procure(rec_id: str, body: ActorBody):
    return handle(lambda: W.procurement_approve(STORE, rec_id, actor_by_name(body.actor)))


@app.post("/api/runs/{run_id}/bulk-approve")
def bulk_approve(run_id: str, body: ActorBody):
    actor = actor_by_name(body.actor)
    if actor.role != W.PLANNER:
        raise HTTPException(403, f"{actor.name} ({actor.role}) cannot perform a planner action.")
    recs = STORE.recs(run_id)
    ids = recs[(recs["status"] == W.PENDING_PLANNER) & (~recs["needs_review"].astype(bool))
               & (recs["action"] != ACTION_REVIEW)]["rec_id"].tolist()
    approved, errors = 0, []
    for rid in ids:
        try:
            W.planner_approve(STORE, rid, actor)
            approved += 1
        except W.WorkflowError as e:
            errors.append(str(e))
    return {"approved": approved, "errors": errors}


@app.post("/api/runs/{run_id}/draft-po")
def draft_po(run_id: str, body: ActorBody):
    try:
        po = W.export_draft_po(STORE, run_id, actor_by_name(body.actor))
    except W.PermissionDenied as e:
        raise HTTPException(403, str(e))
    except W.WorkflowError as e:
        raise HTTPException(409, str(e))
    return JSONResponse(clean({"rows": po, "csv": to_csv_bytes(po, DRAFT_BANNER).decode("utf-8"),
                               "id": po["Draft_PO_ID"].iloc[0]}))


@app.post("/api/signals/{sid}/surface")
def surface(sid: str, body: ReasonBody):
    return handle(lambda: W.analyst_surface(STORE, sid, actor_by_name(body.actor), body.reason))


@app.post("/api/signals/{sid}/dismiss")
def dismiss(sid: str, body: ReasonBody):
    return handle(lambda: W.analyst_dismiss(STORE, sid, actor_by_name(body.actor), body.reason))


@app.post("/api/signals/{sid}/acknowledge")
def acknowledge(sid: str, body: AckBody):
    return handle(lambda: W.procurement_acknowledge(STORE, sid, actor_by_name(body.actor), body.decision, body.note))


# ---------------------------------------------------------------- exports --
def csv_response(data: bytes, name: str) -> Response:
    return Response(data, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{name}"'})


@app.get("/api/runs/{run_id}/recommendations.csv")
def recs_csv(run_id: str):
    return csv_response(to_csv_bytes(recommendations_frame(STORE.recs(run_id))), f"recommendations_{run_id}.csv")


@app.get("/api/runs/{run_id}/audit.csv")
def audit_csv(run_id: str):
    return csv_response(to_csv_bytes(STORE.events(run_id=run_id)), f"audit_{run_id}.csv")


@app.get("/api/validation.csv")
def validation_csv():
    v, _, _ = current()
    return csv_response(to_csv_bytes(v.issues), "validation_findings.csv")


# ------------------------------------------------------------------ web ----
if WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        f = (WEB_DIST / path).resolve()
        if path and f.is_file() and WEB_DIST.resolve() in f.parents:
            return FileResponse(f)
        return FileResponse(WEB_DIST / "index.html")
