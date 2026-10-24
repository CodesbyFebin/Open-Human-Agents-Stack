"""Regression tests for privilege boundaries; no external services required."""
from fastapi.testclient import TestClient
from backend.main import app
from backend.worker import run_isolated, process_job


def test_caller_cannot_self_approve_mcp_tool(monkeypatch):
    monkeypatch.setenv("OPENMINDS_OPERATOR_TOKEN", "test-operator-credential")
    try:
        with TestClient(app) as client:
            result = client.post("/mcp/call", json={"tool": "shell", "approved": True}, headers={"Authorization": "Bearer test-operator-credential"})
        assert result.status_code == 403
    finally:
        pass

def test_mcp_check_does_not_claim_tool_executed(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: USER
    try:
        with TestClient(app) as client:
            result = client.post("/mcp/call", json={"tool": "read_file"}, headers={"Authorization": "Bearer test-operator-credential"})
        assert result.status_code == 200
        assert result.json()["status"] == "capability_checked_not_executed"
    finally:
        app.dependency_overrides.clear()

def test_worker_refuses_unverified_code_job(monkeypatch):
    import backend.worker as worker
    monkeypatch.setattr(worker, "fetch_one", lambda *args: {"status": "queued"})
    result = process_job({"id": "task-1", "org_id": "org-a"})
    assert result["exit"] != 0
    assert "denied" in result["error"]

def test_isolation_uses_docker_without_host_shell(monkeypatch):
    import backend.worker as worker
    seen = {}
    class Result:
        returncode = 0
        stdout = "ok"
        stderr = ""
    def fake_run(argv, **kwargs):
        seen["argv"] = argv
        return Result()
    monkeypatch.setattr(worker.subprocess, "run", fake_run)
    result = run_isolated("print('ok')")
    assert result["exit"] == 0
    args = seen["argv"]
    assert args[0:2] == ["docker", "run"]
    assert "--network" in args and args[args.index("--network") + 1] == "none"
    assert "--read-only" in args
    assert "--cap-drop" in args
    assert "--user" in args
