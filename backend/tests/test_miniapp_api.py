"""Covers the interactive 'try it live' mini-app layer: picking a record, re-running
the workflow against just it, and persisting a simulated action to PostgreSQL."""
import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def executed_session(client):
    resp = client.post("/api/demo", json={"text": "Monitor inventory and alert suppliers when stock falls below 20%."})
    assert resp.status_code == 200
    body = resp.json()
    assert body["outcome"] == "executed"
    return body


def test_demo_result_includes_mini_app_info(executed_session):
    mini_app = executed_session["mini_app"]
    assert mini_app is not None
    assert mini_app["dataset"] == "inventory"
    assert len(mini_app["records"]) == 5  # all inventory.json rows
    assert any(a["action"] == "alert_supplier" for a in mini_app["actions"])


def test_blueprint_outcome_has_no_mini_app(client):
    resp = client.post("/api/demo", json={"text": "analyze employee attendance and identify frequently late employees"})
    assert resp.status_code == 200
    assert resp.json()["outcome"] == "blueprint"
    assert resp.json()["mini_app"] is None


def test_run_single_record_against_workflow(client, executed_session):
    session_id = executed_session["session_id"]
    record_id = executed_session["mini_app"]["records"][0]["id"]  # SKU-100 (Laptop X, low stock)

    resp = client.post(f"/api/demo/{session_id}/records/{record_id}/run")
    assert resp.status_code == 200
    execution = resp.json()
    assert execution["status"] == "success"
    # first step should have read exactly the one filtered record, not all 5
    assert len(execution["step_results"][0]["output"]) == 1


def test_run_record_on_nonexistent_session_returns_404(client):
    resp = client.post("/api/demo/does-not-exist/records/SKU-100/run")
    assert resp.status_code == 404


def test_take_action_persists_and_appears_in_log(client, executed_session):
    session_id = executed_session["session_id"]
    record_id = executed_session["mini_app"]["records"][0]["id"]

    resp = client.post(f"/api/demo/{session_id}/records/{record_id}/actions", json={"action": "alert_supplier"})
    assert resp.status_code == 200
    assert resp.json()["action"] == "alert_supplier"

    log = client.get(f"/api/demo/{session_id}/actions")
    assert log.status_code == 200
    entries = log.json()
    assert any(e["record_id"] == record_id and e["action"] == "alert_supplier" for e in entries)


def test_take_invalid_action_is_rejected(client, executed_session):
    session_id = executed_session["session_id"]
    record_id = executed_session["mini_app"]["records"][0]["id"]

    resp = client.post(f"/api/demo/{session_id}/records/{record_id}/actions", json={"action": "delete_everything"})
    assert resp.status_code == 422
