"""Analytics funnel + trend data (spec §26) must be derived from real client_events,
not hardcoded."""
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


def test_analytics_funnel_counts_increase_after_activity(client, company_headers):
    before = client.get("/api/company/analytics", headers=company_headers).json()
    before_email_count = next(f["count"] for f in before["funnel"] if f["stage"] == "Email Submitted")

    client.post("/api/client/session", json={"email": "analytics-tests@example.com"})

    after = client.get("/api/company/analytics", headers=company_headers).json()
    after_email_count = next(f["count"] for f in after["funnel"] if f["stage"] == "Email Submitted")
    assert after_email_count == before_email_count + 1


def test_analytics_workflow_success_rate_is_a_percentage(client, company_headers):
    body = client.get("/api/company/analytics", headers=company_headers).json()
    assert 0 <= body["workflow_success_rate"] <= 100


def test_analytics_requires_company_auth(client):
    resp = client.get("/api/company/analytics")
    assert resp.status_code == 401
