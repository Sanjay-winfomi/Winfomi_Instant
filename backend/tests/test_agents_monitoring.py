"""Agent + critic monitoring (spec §30-32) - safe operational metadata only, derived
from AgentExecution rows instrumented in graph/orchestrator.py, never raw prompts."""
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


@pytest.fixture(scope="module", autouse=True)
def _seed_a_demo(client):
    session = client.post("/api/client/session", json={"email": "agents-monitoring-tests@example.com"})
    token = session.json()["client_token"]
    client.post(
        "/api/client/demo",
        json={"text": "Review employee expense reports and flag anything over budget."},
        headers={"X-Client-Token": token},
    )


def test_agents_overview_lists_all_four_agents(client, company_headers):
    resp = client.get("/api/company/agents", headers=company_headers)
    assert resp.status_code == 200
    body = resp.json()
    names = {a["agent_name"] for a in body["agents"]}
    assert names == {"requirement", "planner", "critic", "executor"}
    for agent in body["agents"]:
        assert agent["total_executions"] >= 1


def test_agents_overview_includes_critic_metrics(client, company_headers):
    body = client.get("/api/company/agents", headers=company_headers).json()
    assert "critic" in body
    assert 0 <= body["critic"]["average_score"] <= 10


def test_agent_detail_for_known_agent(client, company_headers):
    resp = client.get("/api/company/agents/planner", headers=company_headers)
    assert resp.status_code == 200
    assert resp.json()["agent_name"] == "planner"


def test_agent_detail_rejects_unknown_agent(client, company_headers):
    resp = client.get("/api/company/agents/not-a-real-agent", headers=company_headers)
    assert resp.status_code == 404


def test_agents_requires_company_auth(client):
    resp = client.get("/api/company/agents")
    assert resp.status_code == 401
