"""Persistence for recommendation runs, workflow state and the audit log.

Postgres (Neon) when given a postgres:// URL, SQLite otherwise (local runs and tests).
Queries are written once with `?` placeholders and translated for Postgres.
"""
from __future__ import annotations

import json
import math
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    rule_version TEXT NOT NULL,
    rule_params_json TEXT NOT NULL,
    input_hashes_json TEXT NOT NULL,
    analysis_date TEXT,
    anchor_week TEXT,
    n_recommendations INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS recommendations (
    rec_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    sku_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    action TEXT NOT NULL,
    recommended_qty REAL,
    needs_review INTEGER NOT NULL,
    status TEXT NOT NULL,
    planner_decision TEXT,
    planner_reason TEXT,
    final_action TEXT,
    final_qty REAL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    run_id TEXT NOT NULL,
    rec_id TEXT,
    actor TEXT NOT NULL,
    role TEXT NOT NULL,
    event_type TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT,
    reason TEXT,
    details_json TEXT
);
CREATE TABLE IF NOT EXISTS signals (
    sid TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    sku_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL,
    decision TEXT,
    note TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_recs_run ON recommendations(run_id);
CREATE INDEX IF NOT EXISTS idx_signals_run ON signals(run_id);
CREATE INDEX IF NOT EXISTS idx_events_run ON events(run_id);
"""

# Postgres has no AUTOINCREMENT, and its REAL is single precision.
PG_SCHEMA = (SCHEMA.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY")
             .replace(" REAL", " DOUBLE PRECISION"))

# Insertion order of runs, from the audit log (SQLite's rowid does not exist in Postgres).
RUN_ORDER = "(SELECT MIN(e.event_id) FROM events e WHERE e.run_id = runs.run_id) DESC"


def is_postgres_url(target) -> bool:
    return str(target).startswith(("postgres://", "postgresql://"))


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _json_default(o):
    if hasattr(o, "item"):
        return o.item()
    if o is pd.NA or o is pd.NaT:
        return None
    return str(o)


def to_json(obj) -> str:
    return json.dumps(obj, default=_json_default, allow_nan=True)


def _clean(v):
    """Normalise pandas/numpy scalars for JSON payloads."""
    if v is None or v is pd.NA:
        return None
    if hasattr(v, "item") and not isinstance(v, (list, dict)):
        v = v.item()
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


class _PgConn:
    """Minimal sqlite3-style facade over a psycopg connection: `?` placeholders, dict rows."""

    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql: str, params=()):
        return self.conn.execute(sql.replace("?", "%s"), tuple(params))


class Store:
    def __init__(self, target: Path | str):
        self.pg_url = str(target) if is_postgres_url(target) else None
        self.db_path = "postgres" if self.pg_url else str(target)
        self._mem = None
        self._pg = None
        self._pg_used = 0.0
        self._lock = threading.RLock()
        if self.pg_url:
            with self.tx() as c:
                for stmt in filter(str.strip, PG_SCHEMA.split(";")):
                    c.execute(stmt)
            return
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        else:
            self._mem = sqlite3.connect(":memory:", check_same_thread=False)
        with self.tx() as c:
            c.executescript(SCHEMA)

    def _pg_conn(self):
        """One reused connection; Neon suspends idle computes, so re-check it after a quiet spell."""
        import psycopg
        from psycopg.rows import dict_row

        stale = self._pg is not None and (self._pg.closed or self._pg.broken)
        if self._pg is not None and not stale and time.monotonic() - self._pg_used > 30:
            try:
                self._pg.execute("SELECT 1")
                self._pg.commit()
            except psycopg.Error:
                stale = True
        if self._pg is None or stale:
            if self._pg is not None:
                self._pg.close()
            # prepare_threshold=None: safe behind Neon's pooled (PgBouncer) endpoint.
            self._pg = psycopg.connect(self.pg_url, row_factory=dict_row, prepare_threshold=None, connect_timeout=10)
        return self._pg

    @contextmanager
    def tx(self):
        if self.pg_url:
            with self._lock:
                conn = self._pg_conn()
                try:
                    yield _PgConn(conn)
                    conn.commit()
                except Exception:
                    if not conn.closed:
                        conn.rollback()
                    raise
                finally:
                    self._pg_used = time.monotonic()
            return
        conn = self._mem or sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if self._mem is None:
                conn.close()

    # ---- runs -------------------------------------------------------------
    def create_run(self, recs: pd.DataFrame, *, actor: str, role: str, rule_version: str, rule_params: dict,
                   input_hashes: dict, analysis_date, anchor_week, initial_status: str, routed_status: str) -> str:
        run_id = datetime.now(timezone.utc).strftime("RUN-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
        ts = now_utc()
        with self.tx() as c:
            c.execute("INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?)",
                      (run_id, ts, actor, rule_version, to_json(rule_params), to_json(input_hashes),
                       str(analysis_date) if analysis_date else None, anchor_week, len(recs)))
            c.execute("INSERT INTO events (ts, run_id, rec_id, actor, role, event_type, details_json) VALUES (?,?,?,?,?,?,?)",
                      (ts, run_id, None, actor, role, "run_created",
                       to_json({"rule_version": rule_version, "input_hashes": input_hashes, "n": len(recs)})))
            for rec in recs.to_dict(orient="records"):
                payload = {k: _clean(v) if not isinstance(v, list) else v for k, v in rec.items()}
                rec_id = f"{run_id}:{payload['sku_id']}"
                c.execute("INSERT INTO recommendations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (rec_id, run_id, payload["sku_id"], to_json(payload), payload["action"],
                           payload["recommended_qty"], int(bool(payload["needs_review"])), initial_status,
                           None, None, payload["action"], payload["recommended_qty"], ts))
                c.execute("INSERT INTO events (ts, run_id, rec_id, actor, role, event_type, to_status) VALUES (?,?,?,?,?,?,?)",
                          (ts, run_id, rec_id, actor, role, "generated", initial_status))
                c.execute("UPDATE recommendations SET status=? WHERE rec_id=?", (routed_status, rec_id))
                c.execute("INSERT INTO events (ts, run_id, rec_id, actor, role, event_type, from_status, to_status, details_json) "
                          "VALUES (?,?,?,?,?,?,?,?,?)",
                          (ts, run_id, rec_id, actor, role, "routed", initial_status, routed_status,
                           to_json({"needs_review": bool(payload["needs_review"])})))
        return run_id

    def runs(self) -> pd.DataFrame:
        with self.tx() as c:
            rows = c.execute(f"SELECT * FROM runs ORDER BY {RUN_ORDER}").fetchall()
        return pd.DataFrame([dict(r) for r in rows])

    def latest_run_id(self) -> str | None:
        with self.tx() as c:
            r = c.execute(f"SELECT run_id FROM runs ORDER BY {RUN_ORDER} LIMIT 1").fetchone()
        return r["run_id"] if r else None

    def run(self, run_id: str) -> dict | None:
        with self.tx() as c:
            r = c.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        return dict(r) if r else None

    # ---- recommendations ---------------------------------------------------
    def rec(self, rec_id: str) -> dict | None:
        with self.tx() as c:
            r = c.execute("SELECT * FROM recommendations WHERE rec_id=?", (rec_id,)).fetchone()
        if not r:
            return None
        d = dict(r)
        d["payload"] = json.loads(d.pop("payload_json"))
        return d

    def recs(self, run_id: str) -> pd.DataFrame:
        with self.tx() as c:
            rows = c.execute("SELECT * FROM recommendations WHERE run_id=? ORDER BY sku_id", (run_id,)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            payload = json.loads(d.pop("payload_json"))
            payload.update(d)
            out.append(payload)
        return pd.DataFrame(out)

    def transition(self, rec_id: str, *, actor: str, role: str, event_type: str, from_status: str, to_status: str,
                   reason: str | None = None, details: dict | None = None, **fields) -> None:
        """Atomically update a recommendation and append an audit event (optimistic status check)."""
        ts = now_utc()
        sets = ", ".join([f"{k}=?" for k in fields] + ["status=?", "updated_at=?"])
        with self.tx() as c:
            cur = c.execute(f"UPDATE recommendations SET {sets} WHERE rec_id=? AND status=?",
                            (*fields.values(), to_status, ts, rec_id, from_status))
            if cur.rowcount != 1:
                raise RuntimeError(f"Recommendation {rec_id} is no longer in status '{from_status}'.")
            run_id = rec_id.split(":")[0]
            c.execute("INSERT INTO events (ts, run_id, rec_id, actor, role, event_type, from_status, to_status, reason, details_json) "
                      "VALUES (?,?,?,?,?,?,?,?,?,?)",
                      (ts, run_id, rec_id, actor, role, event_type, from_status, to_status, reason,
                       to_json(details or {})))

    # ---- operations signals (Option C) ------------------------------------
    def add_signals(self, run_id: str, signals: pd.DataFrame, *, actor: str, role: str, status: str) -> None:
        ts = now_utc()
        with self.tx() as c:
            for s in signals.to_dict(orient="records"):
                payload = {k: _clean(v) for k, v in s.items()}
                sid = f"{run_id}|{payload['signal_id']}"
                c.execute("INSERT INTO signals VALUES (?,?,?,?,?,?,?,?,?)",
                          (sid, run_id, payload["sku_id"], to_json(payload), status, None, None, ts, ts))
                c.execute("INSERT INTO events (ts, run_id, rec_id, actor, role, event_type, to_status) VALUES (?,?,?,?,?,?,?)",
                          (ts, run_id, sid, actor, role, "signal_detected", status))

    def signal(self, sid: str) -> dict | None:
        with self.tx() as c:
            r = c.execute("SELECT * FROM signals WHERE sid=?", (sid,)).fetchone()
        if not r:
            return None
        d = dict(r)
        d.update(json.loads(d.pop("payload_json")))
        return d

    def signals(self, run_id: str) -> pd.DataFrame:
        with self.tx() as c:
            rows = c.execute("SELECT * FROM signals WHERE run_id=? ORDER BY sku_id, sid", (run_id,)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d.update(json.loads(d.pop("payload_json")))
            out.append(d)
        return pd.DataFrame(out)

    def transition_signal(self, sid: str, *, actor: str, role: str, event_type: str, from_status: str,
                          to_status: str, reason: str | None = None, **fields) -> None:
        ts = now_utc()
        sets = ", ".join([f"{k}=?" for k in fields] + ["status=?", "updated_at=?"])
        with self.tx() as c:
            cur = c.execute(f"UPDATE signals SET {sets} WHERE sid=? AND status=?",
                            (*fields.values(), to_status, ts, sid, from_status))
            if cur.rowcount != 1:
                raise RuntimeError(f"Signal {sid} is no longer in status '{from_status}'.")
            c.execute("INSERT INTO events (ts, run_id, rec_id, actor, role, event_type, from_status, to_status, reason, details_json) "
                      "VALUES (?,?,?,?,?,?,?,?,?,?)",
                      (ts, sid.split("|")[0], sid, actor, role, event_type, from_status, to_status, reason,
                       to_json(fields)))

    def log_event(self, *, run_id: str, actor: str, role: str, event_type: str, rec_id: str | None = None,
                  reason: str | None = None, details: dict | None = None) -> None:
        with self.tx() as c:
            c.execute("INSERT INTO events (ts, run_id, rec_id, actor, role, event_type, reason, details_json) "
                      "VALUES (?,?,?,?,?,?,?,?)",
                      (now_utc(), run_id, rec_id, actor, role, event_type, reason, to_json(details or {})))

    def events(self, run_id: str | None = None, rec_id: str | None = None) -> pd.DataFrame:
        q, args = "SELECT * FROM events", []
        if rec_id:
            q, args = q + " WHERE rec_id=?", [rec_id]
        elif run_id:
            q, args = q + " WHERE run_id=?", [run_id]
        with self.tx() as c:
            rows = c.execute(q + " ORDER BY event_id", args).fetchall()
        return pd.DataFrame([dict(r) for r in rows])
