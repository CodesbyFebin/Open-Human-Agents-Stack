from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_agent_code_requires_auth():
    r = client.post("/agent/code", json={"task": "test"})
    assert r.status_code == 401

def test_tasks_requires_auth():
    r = client.get("/tasks")
    assert r.status_code == 401
