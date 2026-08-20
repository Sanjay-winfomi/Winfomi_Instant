"""The generic client-event sink (spec §22/§24) - frontend-only events that don't
correspond to a dedicated endpoint call (DEMO_OPENED, FULL_SOLUTION_REQUESTED, ...)."""
import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def client_headers(client):
    resp = client.post("/api/client/session", json={"email": "events-tests@example.com"})
    return {"X-Client-Token": resp.json()["client_token"]}


def test_log_event_accepts_known_event_type(client, client_headers):
    resp = client.post(
        "/api/client/events",
        json={"event_type": "DEMO_OPENED", "metadata": {"session_id": "abc"}},
        headers=client_headers,
    )
    assert resp.status_code == 200


def test_log_event_requires_client_token(client):
    resp = client.post("/api/client/events", json={"event_type": "DEMO_OPENED"})
    assert resp.status_code == 401


def test_full_solution_requested_event_is_logged(client, client_headers):
    resp = client.post(
        "/api/client/events",
        json={"event_type": "FULL_SOLUTION_REQUESTED"},
        headers=client_headers,
    )
    assert resp.status_code == 200
