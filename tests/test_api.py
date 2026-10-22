import importlib
import os

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    for var in ("DATABASE_URL", "GEMINI_API_KEY", "FRESHROOTS_LLM_PROVIDER"):
        monkeypatch.delenv(var, raising=False)
    os.environ["FRESHROOTS_DB_PATH"] = str(tmp_path / "api.db")
    import freshroots.api as api_module
    api_module = importlib.reload(api_module)
    yield TestClient(api_module.app)
    os.environ.pop("FRESHROOTS_DB_PATH", None)


def test_state_payload_from_real_data(client):
    r = client.get("/api/state")
    assert r.status_code == 200
    d = r.json()
    assert d["meta"]["analysis_date"] == "2026-10-19"
    assert len(d["recommendations"]) == 15
    assert len(d["weekly"]) == 240
    assert set(d["readiness"]) == {"roi", "plan", "open_questions", "priority_steps"}
    sku1 = next(x for x in d["recommendations"] if x["sku_id"] == "SKU001")
    assert sku1["recommended_qty"] == 750 and sku1["status"] == "Pending planner review"


def test_workflow_over_http(client):
    run = client.get("/api/state").json()["meta"]["run"]["run_id"]
    assert client.post(f"/api/runs/{run}/bulk-approve", json={"actor": "Priya Sharma"}).status_code == 403
    assert client.post(f"/api/runs/{run}/bulk-approve", json={"actor": "Raghav Kulkarni"}).json()["approved"] == 14
    rec = f"{run}:SKU003"
    assert client.post(f"/api/recs/{rec}/procure", json={"actor": "Raghav Kulkarni"}).status_code == 403
    assert client.post(f"/api/recs/{rec}/procure", json={"actor": "Procurement Officer"}).status_code == 200
    po = client.post(f"/api/runs/{run}/draft-po", json={"actor": "Procurement Officer"}).json()
    assert po["id"].startswith("DRAFT-PO-") and "DRAFT - NOT SUBMITTED" in po["csv"]
    short = {"actor": "Raghav Kulkarni", "action": "Reorder now", "qty": 600, "reason": "short"}
    assert client.post(f"/api/recs/{run}:SKU001/override", json=short).status_code == 409


def test_unknown_actor_and_csv(client):
    run = client.get("/api/state").json()["meta"]["run"]["run_id"]
    assert client.post(f"/api/recs/{run}:SKU001/approve", json={"actor": "Someone Else"}).status_code == 400
    csv = client.get(f"/api/runs/{run}/recommendations.csv")
    assert csv.status_code == 200 and csv.text.startswith("SKU_ID,")
    assert client.get("/api/backtest?h=9").status_code == 400
