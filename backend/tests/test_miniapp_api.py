"""Covers the interactive 'try it live' mini-app layer: picking a record, re-running
the workflow against just it, and persisting a simulated action to PostgreSQL. Uses
the fallback (no LLM key) deterministic synthesizer, so record ids are predictable."""
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
    assert mini_app["dataset"] == "inventory item"
    assert len(mini_app["records"]) == 6  # synthesizer always generates 6 sample records
    assert {a["action"] for a in mini_app["actions"]} == {"approve", "flag_for_review"}


def test_novel_domain_still_produces_a_mini_app(client):
    """No fixed dataset exists for this - proves records are synthesized, not looked up."""
    resp = client.post(
        "/api/demo",
        json={"text": "Track field sales rep visits and flag reps who haven't logged a visit in 14 days."},
    )
    assert resp.status_code == 200
    body = resp.json()
    if body["outcome"] == "executed":
        assert body["mini_app"] is not None
        assert len(body["mini_app"]["records"]) == 6


def test_run_single_record_against_workflow(client, executed_session):
    session_id = executed_session["session_id"]
    record_id = executed_session["mini_app"]["records"][0]["id"]

    resp = client.post(f"/api/demo/{session_id}/records/{record_id}/run")
    assert resp.status_code == 200
    execution = resp.json()
    assert execution["status"] == "success"
    # first step should have read exactly the one filtered record, not all 6
    assert len(execution["step_results"][0]["output"]) == 1
    assert execution["step_results"][0]["output"][0]["id"] == record_id


def test_run_record_on_nonexistent_session_returns_404(client):
    resp = client.post("/api/demo/does-not-exist/records/some-id/run")
    assert resp.status_code == 404


def test_take_action_persists_and_appears_in_log(client, executed_session):
    session_id = executed_session["session_id"]
    record_id = executed_session["mini_app"]["records"][0]["id"]

    resp = client.post(f"/api/demo/{session_id}/records/{record_id}/actions", json={"action": "approve"})
    assert resp.status_code == 200
    assert resp.json()["action"] == "approve"

    log = client.get(f"/api/demo/{session_id}/actions")
    assert log.status_code == 200
    entries = log.json()
    assert any(e["record_id"] == record_id and e["action"] == "approve" for e in entries)


def test_take_invalid_action_is_rejected(client, executed_session):
    session_id = executed_session["session_id"]
    record_id = executed_session["mini_app"]["records"][0]["id"]

    resp = client.post(f"/api/demo/{session_id}/records/{record_id}/actions", json={"action": "delete_everything"})
    assert resp.status_code == 422
