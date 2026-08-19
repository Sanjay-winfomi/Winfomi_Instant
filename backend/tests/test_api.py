from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_and_fetch_demo():
    resp = client.post("/api/demo", json={"text": "Monitor inventory and alert suppliers when stock is low."})
    assert resp.status_code == 200
    body = resp.json()
    assert body["outcome"] in ("executed", "blueprint")
    session_id = body["session_id"]

    fetch = client.get(f"/api/demo/{session_id}")
    assert fetch.status_code == 200
    assert fetch.json()["session_id"] == session_id


def test_fetch_unknown_session_returns_404():
    resp = client.get("/api/demo/does-not-exist")
    assert resp.status_code == 404


def test_demo_rejects_too_short_input():
    resp = client.post("/api/demo", json={"text": "hi"})
    assert resp.status_code == 422


def test_demo_rejects_missing_field():
    resp = client.post("/api/demo", json={})
    assert resp.status_code == 422
