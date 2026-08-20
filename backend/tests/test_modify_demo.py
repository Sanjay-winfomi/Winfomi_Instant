"""Modify/refine an existing demo in natural language (spec §20) - re-enters the same
pipeline against the SAME session_id, carrying the prior requirement's fields forward
rather than discarding a working shape."""
import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def client_headers(client):
    resp = client.post("/api/client/session", json={"email": "modify-tests@example.com"})
    return {"X-Client-Token": resp.json()["client_token"]}


def test_modify_keeps_the_same_session_id(client, client_headers):
    created = client.post(
        "/api/client/demo",
        json={"text": "Monitor customer support tickets and flag urgent ones."},
        headers=client_headers,
    )
    session_id = created.json()["session_id"]

    modified = client.post(
        f"/api/client/demo/{session_id}/modify",
        json={"text": "Also include a priority field on each ticket."},
        headers=client_headers,
    )
    assert modified.status_code == 200
    assert modified.json()["session_id"] == session_id

    fetched = client.get(f"/api/client/demo/{session_id}")
    assert fetched.json()["session_id"] == session_id


def test_modify_unknown_session_returns_404(client, client_headers):
    resp = client.post(
        "/api/client/demo/does-not-exist/modify", json={"text": "change something"}, headers=client_headers
    )
    assert resp.status_code == 404


def test_modify_rejects_too_short_text(client, client_headers):
    created = client.post(
        "/api/client/demo",
        json={"text": "Monitor customer support tickets and flag urgent ones."},
        headers=client_headers,
    )
    session_id = created.json()["session_id"]
    resp = client.post(f"/api/client/demo/{session_id}/modify", json={"text": "x"}, headers=client_headers)
    assert resp.status_code == 422
