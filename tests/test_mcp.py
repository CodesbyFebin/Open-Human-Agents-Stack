from fastapi.testclient import TestClient
from backend.main import app
client = TestClient(app)

def test_mcp_requires_auth(monkeypatch):
    monkeypatch.setenv("OPENMINDS_OPERATOR_TOKEN", "test-operator-credential")
    r = client.post("/mcp/call", json={"tool": "read_file"})
    assert r.status_code == 401
