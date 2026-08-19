import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # runs the lifespan (init_db) once for this module
        yield c


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_and_fetch_demo(client):
    resp = client.post("/api/demo", json={"text": "Monitor inventory and alert suppliers when stock is low."})
    assert resp.status_code == 200
    body = resp.json()
    assert body["outcome"] in ("executed", "blueprint")
    session_id = body["session_id"]

    fetch = client.get(f"/api/demo/{session_id}")
    assert fetch.status_code == 200
    assert fetch.json()["session_id"] == session_id


def test_fetch_unknown_session_returns_404(client):
    resp = client.get("/api/demo/does-not-exist")
    assert resp.status_code == 404


def test_demo_rejects_too_short_input(client):
    resp = client.post("/api/demo", json={"text": "hi"})
    assert resp.status_code == 422


def test_demo_rejects_missing_field(client):
    resp = client.post("/api/demo", json={})
    assert resp.status_code == 422
