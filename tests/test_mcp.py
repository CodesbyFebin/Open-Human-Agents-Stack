from fastapi.testclient import TestClient
from backend.main import app
client = TestClient(app)

def test_mcp_requires_auth():
    r = client.post("/mcp/call", json={"tool": "read_file"})
    assert r.status_code == 401
