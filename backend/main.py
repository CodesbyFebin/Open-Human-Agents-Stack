"""OpenMinds Control Plane v1.0 — Full implementation."""
from __future__ import annotations

import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as aioredis
import structlog
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import text

from backend.db import async_session, init_db
from backend.pipeline.node_pipeline import NodePipelineGenerator
from backend.jobs.job_runner import JobRunner
from backend.security.mcp_auth import MCPAuthenticator
from backend.api.websocket import ConnectionManager

log = structlog.get_logger()


# ─── Schemas ────────────────────────────────────────────────────────────────

class PipelineRequest(BaseModel):
    name: str = "agent_swarm_v1"
    prompt: str = ""
    seed: int = 42

class AgentTaskRequest(BaseModel):
    task: str
    workspace: str = "/tmp/openminds/worktrees"
    max_retries: int = 3

class IssueCreate(BaseModel):
    title: str
    body: str = ""
    assignee_type: str = "agent"
    assignee_id: str | None = None
    squad_id: str | None = None
    priority: int = 3

class ReviewRequest(BaseModel):
    decision: str = Field(pattern="^(approved|rejected|changes_requested)$")
    comment: str = ""
    reviewer_id: str

class JobSubmit(BaseModel):
    type: str
    payload: dict[str, Any] = {}
    idempotency_key: str | None = None
    max_retries: int = 3

class RunnerRegister(BaseModel):
    runner_id: str
    capacity: int = 1
    ip: str = ""
    cert_fingerprint: str = ""


# ─── State ──────────────────────────────────────────────────────────────────

class AppState:
    def __init__(self):
        self.redis: aioredis.Redis | None = None
        self.pipeline_gen: NodePipelineGenerator | None = None
        self.job_runner: JobRunner | None = None
        self.mcp_auth: MCPAuthenticator | None = None
        self.ws_manager: ConnectionManager | None = None
        self._redis_task: asyncio.Task | None = None

state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    state.redis = aioredis.from_url(redis_url, decode_responses=True)
    state.pipeline_gen = NodePipelineGenerator()
    state.job_runner = JobRunner()
    state.mcp_auth = MCPAuthenticator()
    state.ws_manager = ConnectionManager()

    # Start Redis subscriber for cross-instance WebSocket broadcast
    state._redis_task = asyncio.create_task(
        state.ws_manager.start_redis_listener(state.redis)
    )

    log.info("control_plane_started", redis=redis_url)
    yield

    if state._redis_task:
        state._redis_task.cancel()
    if state.redis:
        await state.redis.aclose()
    log.info("control_plane_stopped")


app = FastAPI(title="OpenMinds Control Plane", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ─── Health ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    checks = {"redis": False, "postgres": False}
    if state.redis:
        try:
            checks["redis"] = await state.redis.ping()
        except Exception:
            pass
    try:
        async with async_session() as s:
            await s.execute(text("SELECT 1"))
            checks["postgres"] = True
    except Exception:
        pass

    all_ok = all(checks.values())
    return {
        "status": "operational" if all_ok else "degraded",
        "service": "openminds-control-plane",
        "version": "1.0.0",
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─── Pipeline Execution ─────────────────────────────────────────────────────

@app.post("/pipeline/run")
async def run_pipeline(req: PipelineRequest):
    if not state.pipeline_gen:
        raise HTTPException(503, "Pipeline engine not ready")

    pipeline = state.pipeline_gen.create_pipeline(req.name)
    research = pipeline.add_node("research", "research_agent")
    code = pipeline.add_node("code", "durable_code_agent")
    review = pipeline.add_node("review", "human_review_gate", timeout_seconds=0)
    vault = pipeline.add_node("vault", "storage")
    pipeline.connect(research, code)
    pipeline.connect(code, review)
    pipeline.connect(review, vault)

    context: dict[str, Any] = {"prompt": req.prompt, "seed": req.seed}
    run_id = str(uuid.uuid4())

    result = await state.pipeline_gen.execute(pipeline, context, run_id)

    # Persist trajectory
    async with async_session() as s:
        for i, step in enumerate(result.get("steps", [])):
            await s.execute(text(
                "INSERT INTO trajectories (run_id, agent_or_pipeline, step_index, step_type, output_payload, status) "
                "VALUES (:run_id, :pipeline, :idx, :type, :output, :status)"
            ), {
                "run_id": run_id, "pipeline": req.name, "idx": i,
                "type": step["type"], "output": json.dumps(step), "status": step["status"],
            })
        await s.commit()

    # Publish event
    await state.redis.publish("openminds:events", json.dumps({
        "type": "pipeline_completed", "run_id": run_id, "status": result["status"]
    }))

    return {"run_id": run_id, "status": result["status"], "steps": result["steps"]}


# ─── Durable Agent (Job-based) ─────────────────────────────────────────────

@app.post("/agent/code")
async def schedule_coding_agent(req: AgentTaskRequest):
    job_id = await state.job_runner.submit(
        type="coding_task",
        payload={"task": req.task, "workspace": req.workspace},
        max_retries=req.max_retries,
    )
    await state.redis.publish("openminds:events", json.dumps({
        "type": "job_submitted", "job_id": job_id, "type": "coding_task"
    }))
    return {"job_id": job_id, "status": "accepted", "max_retries": req.max_retries}


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    async with async_session() as s:
        row = await s.execute(
            text("SELECT * FROM jobs WHERE id = :id"), {"id": job_id}
        )
        job = row.mappings().first()
    if not job:
        raise HTTPException(404, "Job not found")
    return dict(job)


@app.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    async with async_session() as s:
        result = await s.execute(
            text("UPDATE jobs SET status='cancelled', completed_at=now() WHERE id=:id AND status IN ('pending','claimed','running') RETURNING id"),
            {"id": job_id},
        )
        await s.commit()
        if result.rowcount == 0:
            raise HTTPException(409, "Job cannot be cancelled (already terminal)")
    return {"job_id": job_id, "status": "cancelled"}


# ─── Board ──────────────────────────────────────────────────────────────────

@app.post("/board/issues")
async def create_issue(issue: IssueCreate):
    async with async_session() as s:
        result = await s.execute(
            text("INSERT INTO issues (title, body, assignee_type, assignee_id, squad_id, priority) "
                 "VALUES (:t,:b,:at,:ai,:sq,:p) RETURNING id, created_at"),
            {"t": issue.title, "b": issue.body, "at": issue.assignee_type,
             "ai": uuid.UUID(issue.assignee_id) if issue.assignee_id else None,
             "sq": uuid.UUID(issue.squad_id) if issue.squad_id else None, "p": issue.priority},
        )
        await s.commit()
        row = result.mappings().first()
    issue_id = str(row["id"])
    await state.redis.publish("openminds:events", json.dumps({
        "type": "issue_created", "issue_id": issue_id
    }))
    return {"issue_id": issue_id, "status": "open"}


@app.get("/board/issues")
async def list_issues(status: str | None = None, squad_id: str | None = None):
    query = "SELECT * FROM issues WHERE 1=1"
    params: dict = {}
    if status:
        query += " AND status = :status"
        params["status"] = status
    if squad_id:
        query += " AND squad_id = :squad_id"
        params["squad_id"] = squad_id
    query += " ORDER BY created_at DESC LIMIT 100"

    async with async_session() as s:
        rows = await s.execute(text(query), params)
        issues = [dict(r) for r in rows.mappings().all()]
    return {"issues": issues, "count": len(issues)}


@app.post("/board/issues/{issue_id}/review")
async def review_issue(issue_id: str, review: ReviewRequest):
    """Server-side review gate. Only reviewers/admins can approve."""
    async with async_session() as s:
        # Verify reviewer role
        role_row = await s.execute(
            text("SELECT role FROM users WHERE id = :id"), {"id": review.reviewer_id}
        )
        role = role_row.scalar_one_or_none()
        if role not in ("reviewer", "admin"):
            raise HTTPException(403, "Only reviewers or admins can make review decisions")

        # Record decision
        await s.execute(
            text("INSERT INTO review_decisions (issue_id, reviewer_id, decision, comment) VALUES (:i,:r,:d,:c)"),
            {"i": issue_id, "r": review.reviewer_id, "d": review.decision, "c": review.comment},
        )

        # Update issue status
        new_status = "closed" if review.decision == "approved" else "open"
        await s.execute(
            text("UPDATE issues SET status=:s, updated_at=now() WHERE id=:i"),
            {"s": new_status, "i": issue_id},
        )
        await s.commit()

    await state.redis.publish("openminds:events", json.dumps({
        "type": "issue_reviewed", "issue_id": issue_id, "decision": review.decision
    }))
    return {"issue_id": issue_id, "decision": review.decision, "status": new_status}


# ─── MCP Tool Authorization ─────────────────────────────────────────────────

@app.post("/mcp/approve-tool")
async def approve_mcp_tool(tool_name: str, approved_by: str, scope: str = "*"):
    """Admin grants approval for a tool. Stored durably in Postgres."""
    await state.mcp_auth.approve(tool_name, approved_by, scope)
    return {"tool_name": tool_name, "status": "approved"}


@app.get("/mcp/tool-status/{tool_name}")
async def mcp_tool_status(tool_name: str):
    approved = await state.mcp_auth.is_approved(tool_name)
    return {"tool_name": tool_name, "approved": approved}


# ─── Runner Fleet ───────────────────────────────────────────────────────────

@app.post("/runners/register")
async def register_runner(runner: RunnerRegister):
    async with async_session() as s:
        await s.execute(
            text("INSERT INTO runners (runner_id, ip, capacity, cert_fingerprint) "
                 "VALUES (:rid,:ip,:cap,:cert) ON CONFLICT (runner_id) DO UPDATE SET status='active', last_heartbeat=now()"),
            {"rid": runner.runner_id, "ip": runner.ip, "cap": runner.capacity, "cert": runner.cert_fingerprint},
        )
        await s.commit()
    await state.redis.publish("openminds:events", json.dumps({"type": "runner_registered", "runner_id": runner.runner_id}))
    return {"runner_id": runner.runner_id, "status": "registered"}


@app.get("/runners")
async def list_runners():
    async with async_session() as s:
        rows = await s.execute(text("SELECT * FROM runners WHERE status != 'decommissioned'"))
        runners = [dict(r) for r in rows.mappings().all()]
    return {"runners": runners, "count": len(runners)}


# ─── Telemetry ──────────────────────────────────────────────────────────────

@app.get("/telemetry/summary")
async def telemetry_summary():
    async with async_session() as s:
        runners = (await s.execute(text("SELECT COUNT(*) as c FROM runners WHERE status='active'"))).scalar()
        trajectories = (await s.execute(text("SELECT COUNT(*) as c FROM trajectories"))).scalar()
        open_issues = (await s.execute(text("SELECT COUNT(*) as c FROM issues WHERE status='open'"))).scalar()
        jobs_pending = (await s.execute(text("SELECT COUNT(*) as c FROM jobs WHERE status IN ('pending','running')"))).scalar()
    return {
        "active_runners": runners or 0,
        "trajectories_recorded": trajectories or 0,
        "issues_open": open_issues or 0,
        "jobs_active": jobs_pending or 0,
        "circuit_breaker": "unknown",
        "event_mesh": state.ws_manager.status() if state.ws_manager else {"subscriber_connected": False},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─── WebSocket: Live Telemetry Stream ───────────────────────────────────────

@app.websocket("/ws/telemetry")
async def ws_telemetry(websocket: WebSocket):
    await state.ws_manager.connect(websocket)
    try:
        while True:
            # Keep-alive: client can send ping
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        state.ws_manager.disconnect(websocket)
