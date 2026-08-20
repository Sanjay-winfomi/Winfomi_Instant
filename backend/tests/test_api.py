import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # runs the lifespan (init_db) once for this module
        yield c


@pytest.fixture(scope="module")
def client_headers(client):
    resp = client.post("/api/client/session", json={"email": "api-tests@example.com"})
    assert resp.status_code == 200
    return {"X-Client-Token": resp.json()["client_token"]}


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_and_fetch_demo(client, client_headers):
    resp = client.post(
        "/api/client/demo",
        json={"text": "Monitor inventory and alert suppliers when stock is low."},
        headers=client_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["outcome"] in ("executed", "blueprint")
    session_id = body["session_id"]

    fetch = client.get(f"/api/client/demo/{session_id}")
    assert fetch.status_code == 200
    assert fetch.json()["session_id"] == session_id


def test_fetch_unknown_session_returns_404(client):
    resp = client.get("/api/client/demo/does-not-exist")
    assert resp.status_code == 404


def test_demo_rejects_too_short_input(client, client_headers):
    resp = client.post("/api/client/demo", json={"text": "hi"}, headers=client_headers)
    assert resp.status_code == 422


def test_demo_rejects_missing_field(client, client_headers):
    resp = client.post("/api/client/demo", json={}, headers=client_headers)
    assert resp.status_code == 422


def test_demo_requires_client_token(client):
    resp = client.post("/api/client/demo", json={"text": "Monitor inventory and alert suppliers."})
    assert resp.status_code == 401
