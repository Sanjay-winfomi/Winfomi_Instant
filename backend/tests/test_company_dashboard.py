"""Dashboard KPIs must reflect real stored data (spec §25), not hardcoded numbers."""
import uuid

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


def test_dashboard_reflects_a_freshly_created_demo(client, company_headers):
    before = client.get("/api/company/dashboard", headers=company_headers).json()

    session = client.post("/api/client/session", json={"email": f"dashboard-tests-{uuid.uuid4().hex[:8]}@example.com"})
    token = session.json()["client_token"]
    client.post(
        "/api/client/demo",
        json={"text": "Track vendor delivery delays and flag chronic offenders."},
        headers={"X-Client-Token": token},
    )

    after = client.get("/api/company/dashboard", headers=company_headers).json()
    assert after["total_demos"] == before["total_demos"] + 1
    assert after["total_leads"] >= before["total_leads"] + 1


def test_dashboard_success_rate_is_between_0_and_100(client, company_headers):
    body = client.get("/api/company/dashboard", headers=company_headers).json()
    assert 0 <= body["demo_success_rate"] <= 100
    assert 0 <= body["qualified_lead_rate"] <= 100


def test_dashboard_requires_company_auth(client):
    resp = client.get("/api/company/dashboard")
    assert resp.status_code == 401
