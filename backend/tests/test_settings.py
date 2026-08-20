"""Company settings (spec §35) - only the 3 non-secret tuning values are DB-writable,
and a change must actually affect a subsequent pipeline run (services/settings_service.py)."""
import pytest
from fastapi.testclient import TestClient

from core.config import get_settings
from graph.orchestrator import run_pipeline
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


def test_read_settings_returns_env_defaults_when_no_override(client, company_headers):
    resp = client.get("/api/company/settings", headers=company_headers)
    assert resp.status_code == 200
    assert resp.json()["critic_approval_threshold"] > 0


def test_update_settings_persists_and_is_reflected_on_read(client, company_headers):
    resp = client.put(
        "/api/company/settings",
        json={"critic_approval_threshold": 2.0, "max_planner_retries": 1},
        headers=company_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["critic_approval_threshold"] == 2.0
    assert resp.json()["max_planner_retries"] == 1

    read_back = client.get("/api/company/settings", headers=company_headers).json()
    assert read_back["critic_approval_threshold"] == 2.0

    # restore a sane default so later tests in the suite aren't affected
    client.put("/api/company/settings", json={"critic_approval_threshold": 8.0, "max_planner_retries": 2}, headers=company_headers)


def test_lowering_the_threshold_affects_a_subsequent_pipeline_run(client, company_headers):
    client.put("/api/company/settings", json={"critic_approval_threshold": 0.0}, headers=company_headers)
    try:
        state = run_pipeline("Summarize weekly sales calls by outcome.")
        assert state["critic"].approved is True
    finally:
        client.put("/api/company/settings", json={"critic_approval_threshold": 8.0}, headers=company_headers)


def test_settings_requires_company_auth(client):
    resp = client.get("/api/company/settings")
    assert resp.status_code == 401
