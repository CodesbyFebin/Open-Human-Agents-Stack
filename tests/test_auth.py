from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_agent_code_requires_auth(monkeypatch):
    monkeypatch.setenv("OPENMINDS_OPERATOR_TOKEN", "test-operator-credential")
    r = client.post("/agent/code", json={"task": "test"})
    assert r.status_code == 401

def test_tasks_requires_auth(monkeypatch):
    monkeypatch.setenv("OPENMINDS_OPERATOR_TOKEN", "test-operator-credential")
    r = client.get("/tasks")
    assert r.status_code == 401

def test_arbitrary_bearer_token_not_accepted(monkeypatch):
    monkeypatch.setenv("OPENMINDS_OPERATOR_TOKEN", "test-operator-credential")
    r = client.get("/integrations/catalog", headers={"Authorization": "Bearer anything"})
    assert r.status_code == 401

def test_unconfigured_auth_fails_closed(monkeypatch):
    monkeypatch.delenv("OPENMINDS_OPERATOR_TOKEN", raising=False)
    r = client.get("/integrations/catalog")
    assert r.status_code == 503

def test_authenticated_catalog_reports_unconfigured_services(monkeypatch):
    monkeypatch.setenv("OPENMINDS_OPERATOR_TOKEN", "test-operator-credential")
    r = client.get("/integrations/catalog",
                   headers={"Authorization": "Bearer test-operator-credential"})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 20
    assert all(x["runtime_status"] == "unconfigured" for x in body["integrations"])
