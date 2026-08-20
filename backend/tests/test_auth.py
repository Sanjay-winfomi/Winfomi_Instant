"""Company-portal auth: login, JWT validation, and that /api/company/* is genuinely
enforced server-side (spec §3/§38) - never trust a frontend's own claim of role."""
import pytest
from fastapi.testclient import TestClient

from core.config import get_settings
from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_seed_admin_can_log_in(client):
    settings = get_settings()
    resp = client.post(
        "/api/company/auth/login",
        json={"email": settings.seed_admin_email, "password": settings.seed_admin_password},
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_login_rejects_wrong_password(client):
    settings = get_settings()
    resp = client.post(
        "/api/company/auth/login",
        json={"email": settings.seed_admin_email, "password": "definitely-wrong"},
    )
    assert resp.status_code == 401


def test_login_rejects_unknown_email(client):
    resp = client.post("/api/company/auth/login", json={"email": "nobody@nowhere.com", "password": "x"})
    assert resp.status_code == 401


def test_company_route_rejects_missing_token(client):
    resp = client.get("/api/company/dashboard")
    assert resp.status_code == 401


def test_company_route_rejects_garbage_token(client):
    resp = client.get("/api/company/dashboard", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_company_route_accepts_valid_token(client):
    settings = get_settings()
    login = client.post(
        "/api/company/auth/login",
        json={"email": settings.seed_admin_email, "password": settings.seed_admin_password},
    )
    token = login.json()["access_token"]
    resp = client.get("/api/company/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert "total_leads" in resp.json()


def test_me_returns_current_user(client):
    settings = get_settings()
    login = client.post(
        "/api/company/auth/login",
        json={"email": settings.seed_admin_email, "password": settings.seed_admin_password},
    )
    token = login.json()["access_token"]
    resp = client.get("/api/company/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "COMPANY_ADMIN"
