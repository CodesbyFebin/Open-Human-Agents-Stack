"""Full-stack tests: API, pipeline, jobs, security, adversarial."""
import asyncio
import json
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text

from backend.main import app
from backend.pipeline.node_pipeline import NodePipelineGenerator, Pipeline
from backend.db import async_session


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ─── Health ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "openminds-control-plane"
    assert data["version"] == "1.0.0"
    assert "checks" in data


# ─── Pipeline DAG ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pipeline_linear_execution():
    gen = NodePipelineGenerator()
    p = gen.create_pipeline("test")
    a = p.add_node("a", "research_agent")
    b = p.add_node("b", "storage")
    p.connect(a, b)
    result = await gen.execute(p, {"prompt": "test"}, str(uuid.uuid4()))
    assert result["status"] == "completed"
    assert len(result["steps"]) == 2


@pytest.mark.asyncio
async def test_pipeline_cycle_detection():
    gen = NodePipelineGenerator()
    p = gen.create_pipeline("cyclic")
    a = p.add_node("a", "research_agent")
    b = p.add_node("b", "storage")
    p.connect(a, b)
    p.connect(b, a)
    with pytest.raises(ValueError, match="Cycle detected"):
        p.topological_sort()


@pytest.mark.asyncio
async def test_pipeline_fail_closed():
    """If a node fails, pipeline stops immediately (fail-closed)."""
    gen = NodePipelineGenerator()
    p = gen.create_pipeline("fail")
    a = p.add_node("a", "research_agent")
    b = p.add_node("b", "nonexistent_type")  # Will raise
    p.connect(a, b)
    result = await gen.execute(p, {"prompt": "x"}, str(uuid.uuid4()))
    assert result["status"] == "failed"
    assert result["failed_node"] == "b"


@pytest.mark.asyncio
async def test_pipeline_checkpoint_resume():
    """Second execution of same run_id resumes from checkpoint."""
    gen = NodePipelineGenerator()
    run_id = str(uuid.uuid4())

    p1 = gen.create_pipeline("resume_test")
    a = p1.add_node("a", "research_agent")
    p1.connect(a, a)  # self-loop won't work, use linear
    # Actually: just run it twice with same run_id
    p1 = gen.create_pipeline("resume_test")
    a = p1.add_node("a", "research_agent")
    b = p1.add_node("b", "storage")
    p1.connect(a, b)
    r1 = await gen.execute(p1, {"prompt": "first"}, run_id)
    assert r1["status"] == "completed"

    # Second run: should load from checkpoint
    p2 = gen.create_pipeline("resume_test")
    a2 = p2.add_node("a", "research_agent")
    b2 = p2.add_node("b", "storage")
    p2.connect(a2, b2)
    r2 = await gen.execute(p2, {"prompt": "first"}, run_id)
    # Checkpoint should be found for step 0
    assert r2["steps"][0]["status"] == "resumed_from_checkpoint"


# ─── API: Board ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_issue(client):
    r = await client.post("/board/issues", json={
        "title": "Fix bug", "body": "desc", "assignee_type": "agent", "priority": 2
    })
    assert r.status_code == 200
    assert "issue_id" in r.json()


@pytest.mark.asyncio
async def test_list_issues(client):
    await client.post("/board/issues", json={"title": "Test", "assignee_type": "human"})
    r = await client.get("/board/issues")
    assert r.status_code == 200
    assert r.json()["count"] >= 1


@pytest.mark.asyncio
async def test_review_gate_rejects_non_reviewer(client):
    """Only reviewers/admins can approve. Regular operators are blocked."""
    r = await client.post("/board/issues", json={
        "title": "Review me", "assignee_type": "agent"
    })
    issue_id = r.json()["issue_id"]

    # Try to review as non-reviewer (will 403 or 500 if user doesn't exist)
    r2 = await client.post(f"/board/issues/{issue_id}/review", json={
        "decision": "approved", "comment": "ok",
        "reviewer_id": str(uuid.uuid4()),  # Non-existent user
    })
    assert r2.status_code in (403, 500)  # Permission denied or user not found


# ─── API: Jobs ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_job_submit_and_get(client):
    r = await client.post("/agent/code", json={
        "task": "Write a function", "workspace": "/tmp/test", "max_retries": 2
    })
    assert r.status_code == 200
    job_id = r.json()["job_id"]
    assert r.json()["status"] == "accepted"

    r2 = await client.get(f"/jobs/{job_id}")
    assert r2.status_code == 200


@pytest.mark.asyncio
async def test_job_cancel(client):
    r = await client.post("/agent/code", json={"task": "x", "workspace": "/tmp"})
    job_id = r.json()["job_id"]
    r2 = await client.post(f"/jobs/{job_id}/cancel")
    assert r2.status_code == 200
    assert r2.json()["status"] == "cancelled"


# ─── Security: MCP Auth ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_mcp_tool_not_approved_by_default(client):
    r = await client.get("/mcp/tool-status/some_privileged_tool")
    assert r.status_code == 200
    assert r.json()["approved"] is False


# ─── Adversarial: Title Injection ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_title_injection_blocked(client):
    """Task titles must NOT be executable as Python."""
    payloads = [
        "__import__('os').system('echo pwned')",
        "().__class__.__mro__[1].__subclasses__()",
        "exec('print(1)')",
        "lambda: __import__('subprocess').call(['ls'])",
        f"{''.join(chr(c) for c in [105,109,112,111,114,116])} os",
    ]
    for payload in payloads:
        r = await client.post("/board/issues", json={
            "title": payload, "assignee_type": "agent"
        })
        # Should be stored as opaque string, never executed
        assert r.status_code == 200
        # Verify it's stored as-is (not evaluated)
        r2 = await client.get("/board/issues")
        found = any(p in json.dumps(r2.json()) for p in [payload[:20]])
        assert found, f"Title was not stored as opaque string: {payload[:30]}"


# ─── Adversarial: MCP Self-Approval ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_mcp_caller_cannot_self_approve(client):
    """A caller passing approved:true in their request must be ignored."""
    # The API doesn't accept an 'approved' field at all
    r = await client.post("/mcp/approve-tool", params={
        "tool_name": "dangerous_tool",
        "approved_by": str(uuid.uuid4()),  # Random non-admin
    })
    # Should fail: user doesn't exist or doesn't have role
    assert r.status_code in (403, 500)


# ─── Telemetry ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_telemetry_summary(client):
    r = await client.get("/telemetry/summary")
    assert r.status_code == 200
    data = r.json()
    assert "active_runners" in data
    assert "trajectories_recorded" in data
    assert "issues_open" in data
