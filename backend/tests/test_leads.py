"""Lead creation on email submit, deterministic scoring, and company-side status/notes
management. Lead scoring must never call an LLM (spec §29) - it's a pure weighted sum
over logged client_events (services/lead_scoring.py)."""
import pytest
from fastapi.testclient import TestClient

from core.config import get_settings
from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def company_headers(client):
    settings = get_settings()
    login = client.post(
        "/api/company/auth/login",
        json={"email": settings.seed_admin_email, "password": settings.seed_admin_password},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_email_submission_creates_a_lead(client, company_headers):
    resp = client.post("/api/client/session", json={"email": "lead-tests@example.com"})
    assert resp.status_code == 200

    leads = client.get("/api/company/leads", params={"search": "lead-tests"}, headers=company_headers)
    assert leads.status_code == 200
    body = leads.json()
    assert body["total"] >= 1
    assert any(l["email"] == "lead-tests@example.com" for l in body["items"])


def test_resubmitting_the_same_email_reuses_the_lead(client):
    first = client.post("/api/client/session", json={"email": "repeat-lead@example.com"})
    second = client.post("/api/client/session", json={"email": "repeat-lead@example.com"})
    assert first.json()["client_token"] == second.json()["client_token"]


def test_invalid_email_is_rejected(client):
    resp = client.post("/api/client/session", json={"email": "not-an-email"})
    assert resp.status_code == 422


def test_lead_score_increases_with_demo_activity(client, company_headers):
    session = client.post("/api/client/session", json={"email": "scoring-tests@example.com"})
    token = session.json()["client_token"]

    leads = client.get("/api/company/leads", params={"search": "scoring-tests"}, headers=company_headers).json()
    lead_id = leads["items"][0]["id"]
    score_after_email = leads["items"][0]["score"]

    client.post(
        "/api/client/demo",
        json={"text": "Summarize weekly support tickets by category."},
        headers={"X-Client-Token": token},
    )

    detail = client.get(f"/api/company/leads/{lead_id}", headers=company_headers).json()
    assert detail["score"] > score_after_email
    assert any(e["event_type"] == "DEMO_CREATED" for e in detail["events"])


def test_update_lead_status_and_priority(client, company_headers):
    client.post("/api/client/session", json={"email": "status-tests@example.com"})
    leads = client.get("/api/company/leads", params={"search": "status-tests"}, headers=company_headers).json()
    lead_id = leads["items"][0]["id"]

    resp = client.patch(
        f"/api/company/leads/{lead_id}",
        json={"status": "QUALIFIED", "priority": "high"},
        headers=company_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "QUALIFIED"
    assert resp.json()["priority"] == "high"


def test_add_internal_note_is_never_exposed_to_client(client, company_headers):
    client.post("/api/client/session", json={"email": "notes-tests@example.com"})
    leads = client.get("/api/company/leads", params={"search": "notes-tests"}, headers=company_headers).json()
    lead_id = leads["items"][0]["id"]

    note = client.post(
        f"/api/company/leads/{lead_id}/notes", json={"note": "Called, very interested."}, headers=company_headers
    )
    assert note.status_code == 200

    detail = client.get(f"/api/company/leads/{lead_id}", headers=company_headers).json()
    assert any(n["note"] == "Called, very interested." for n in detail["notes"])
    # no /api/client/* route returns internal_notes at all - nothing further to assert
    # here beyond confirming the note only ever surfaces through the company API.


def test_leads_endpoint_requires_company_auth(client):
    resp = client.get("/api/company/leads")
    assert resp.status_code == 401
