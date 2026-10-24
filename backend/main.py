"""OpenMinds Control Plane — working entry with auth on privileged routes."""
from __future__ import annotations
import json, uuid, os, secrets
from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

from backend.pipeline.node_pipeline import NodePipelineGenerator, build_example_agent_swarm_pipeline
from agents.durable_worker import DurableCoderAgent, CodingTaskOutput

app = FastAPI(title="OpenMinds Control Plane", version="2.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class State:
    redis = None
    pipeline = NodePipelineGenerator()
    trajectories: list = []
    issues: list = []
    runners: dict = {}

state = State()

@app.on_event("startup")
async def startup():
    import os
    if aioredis:
        try:
            state.redis = aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
        except Exception:
            state.redis = None

def require_auth(authorization: Optional[str] = Header(None)):
    # Temporary single-operator gate. Replace with tenant-scoped, revocable
    # sessions before enabling multi-user or third-party integrations.
    expected = os.getenv("OPENMINDS_OPERATOR_TOKEN", "")
    if not expected:
        raise HTTPException(503, "Authentication not configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing Bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if not secrets.compare_digest(token, expected):
        raise HTTPException(401, "Invalid token")
    return "operator"

class PipelineRequest(BaseModel):
    name: str = "agent_swarm_v1"
    prompt: str = ""
    seed: int = 42

class AgentTaskRequest(BaseModel):
    task: str
    workspace: str = "/tmp/openminds/worktrees"

class IssueCreate(BaseModel):
    title: str
    body: str = ""
    assignee_type: str = "agent"
    assignee_id: str = ""

@app.get("/health")
async def health():
    redis_ok = False
    if state.redis:
        try:
            redis_ok = await state.redis.ping()
        except Exception:
            pass
    return {
        "status": "operational" if redis_ok or state.redis is None else "degraded",
        "service": "openminds-control-plane",
        "version": "2.3.0",
        "redis": redis_ok,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.post("/pipeline/run")
async def run_pipeline(req: PipelineRequest, _=Depends(require_auth)):
    pipeline = build_example_agent_swarm_pipeline(state.pipeline)
    traj = str(uuid.uuid4())
    result = await state.pipeline.execute(pipeline, {"prompt": req.prompt}, traj)
    state.trajectories.append({"trajectory_id": traj, "status": result.get("status"), "steps": result.get("steps", [])})
    return {"trajectory_id": traj, "status": result.get("status"), "steps_executed": len(result.get("steps", [])), "result": result}

@app.post("/agent/code")
async def schedule_coding_agent(req: AgentTaskRequest, _=Depends(require_auth)):
    task_id = str(uuid.uuid4())
    agent = DurableCoderAgent(workspace=req.workspace)
    output: CodingTaskOutput = await agent.run(req.task)
    state.trajectories.append({"trajectory_id": task_id, "status": "recorded", "diff": output.diff})
    return {"task_id": task_id, "status": "recorded", "accepted": True, "summary": output.summary}

@app.post("/board/issues")
async def create_issue(issue: IssueCreate, _=Depends(require_auth)):
    iid = str(uuid.uuid4())
    rec = {"id": iid, "title": issue.title, "body": issue.body, "status": "open",
           "assignee_type": issue.assignee_type, "assignee_id": issue.assignee_id,
           "created_at": datetime.now(timezone.utc).isoformat()}
    state.issues.append(rec)
    return {"issue_id": iid, "status": "created"}

@app.get("/board/issues")
async def list_issues(_=Depends(require_auth)):
    return {"issues": state.issues, "count": len(state.issues)}

@app.post("/board/issues/{issue_id}/review")
async def review_issue(issue_id: str, decision: str, comment: str = "", _=Depends(require_auth)):
    if decision not in ("approved", "rejected"):
        raise HTTPException(400, "decision must be approved or rejected")
    for issue in state.issues:
        if issue["id"] == issue_id:
            issue["status"] = "closed" if decision == "approved" else "open"
            issue["review_decision"] = decision
            issue["review_comment"] = comment
            return {"issue_id": issue_id, "decision": decision, "status": issue["status"]}
    raise HTTPException(404, "Issue not found")

@app.get("/telemetry/summary")
async def telemetry_summary(_=Depends(require_auth)):
    return {
        "active_runners": len(state.runners),
        "trajectories_recorded": len(state.trajectories),
        "issues_open": len([i for i in state.issues if i["status"] == "open"]),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.post("/runners/register")
async def register_runner(runner_id: str, capacity: int = 1, _=Depends(require_auth)):
    state.runners[runner_id] = {"runner_id": runner_id, "capacity": capacity, "status": "active"}
    return {"runner_id": runner_id, "status": "registered"}


@app.get("/integrations/catalog")
async def integrations_catalog(_=Depends(require_auth)):
    """License-aware integration registry; no live connection status implied."""
    from backend.integrations.catalog import public_integrations
    items = public_integrations()
    return {"integrations": items, "count": len(items), "runtime_status": "not_probed"}
