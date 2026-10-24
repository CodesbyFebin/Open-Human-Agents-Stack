"""
OpenMinds Control Plane — FastAPI entry (P0 foundation)
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
import logging
from .auth import get_current_user
from .db import execute, fetch_all, fetch_one

log = logging.getLogger("openminds")
app = FastAPI(title="OpenMinds Control Plane", version="2.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PipelineRequest(BaseModel):
    name: str = "agent_swarm_v1"
    prompt: Optional[str] = "cinematic agent swarm evidence"
    seed: int = 42

class AgentTask(BaseModel):
    task: str
    workspace: Optional[str] = "/tmp/openminds"

@app.get("/health")
def health():
    return {"status": "operational", "service": "openminds-control-plane", "version": "2.2.0"}

@app.post("/pipeline/run")
async def run_pipeline(req: PipelineRequest, user=Depends(get_current_user)):
    try:
        from backend.pipeline.node_pipeline import NodePipelineGenerator, build_example_agent_swarm_pipeline
        from backend.pipeline.comfy_graph import ComfyGraphExecutor
        generator = NodePipelineGenerator(ComfyGraphExecutor("localhost:8188"))
        graph = build_example_agent_swarm_pipeline(generator)
        result = await generator.execute(graph, {"prompt": req.prompt})
        return {"graph_id": getattr(graph, "id", str(uuid.uuid4())), "status": "executed", "result": result, "org_id": str(user["org_id"])}
    except Exception as e:
        log.exception("pipeline execution failed")
        raise HTTPException(status_code=503, detail=f"Pipeline engine unavailable: {e}")

@app.post("/agent/code")
async def run_code_agent(task: AgentTask, user=Depends(get_current_user)):
    task_id = str(uuid.uuid4())
    execute(
        """INSERT INTO tasks (id, org_id, title, status, workspace, created_by)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (task_id, user["org_id"], task.task, "pending", task.workspace, user["id"])
    )
    return {
        "task_id": task_id,
        "status": "persisted",
        "agent": "durable_coder",
        "message": "Task recorded in PostgreSQL. Isolated worker dispatch is next.",
        "org_id": str(user["org_id"])
    }

@app.get("/tasks")
async def list_tasks(user=Depends(get_current_user)):
    rows = fetch_all(
        "SELECT id, title, status, workspace, created_at FROM tasks WHERE org_id = %s ORDER BY created_at DESC LIMIT 50",
        (user["org_id"],)
    )
    return {"tasks": rows, "org_id": str(user["org_id"])}

@app.get("/telemetry/summary")
async def telemetry_summary(user=Depends(get_current_user)):
    count = fetch_one("SELECT COUNT(*) AS n FROM tasks WHERE org_id = %s", (user["org_id"],))
    return {
        "active_runners": 0,
        "circuit_status": "unknown",
        "cost_usd_today": 0.0,
        "trajectories": count["n"] if count else 0,
        "note": "Live runner aggregation pending; task count is real"
    }

from .mcp_gate import check as mcp_check
from .queue import enqueue
from .db import execute as db_execute

class MCPCall(BaseModel):
    tool: str
    approved: bool = False

class Approval(BaseModel):
    decision: str  # approved | rejected

@app.post("/mcp/call")
async def mcp_call(body: MCPCall, user=Depends(get_current_user)):
    mcp_check(body.tool, user["role"], body.approved)
    return {"tool": body.tool, "status": "allowed", "org_id": str(user["org_id"])}

@app.post("/tasks/{task_id}/approve")
async def approve_task(task_id: str, body: Approval, user=Depends(get_current_user)):
    if user["role"] not in ("admin", "reviewer", "member"):
        raise HTTPException(403, "Cannot approve")
    db_execute(
        "INSERT INTO approvals (task_id, reviewer_id, decision) VALUES (%s, %s, %s)",
        (task_id, user["id"], body.decision)
    )
    new_status = "approved" if body.decision == "approved" else "rejected"
    db_execute("UPDATE tasks SET status=%s, updated_at=now() WHERE id=%s AND org_id=%s",
               (new_status, task_id, user["org_id"]))
    return {"task_id": task_id, "decision": body.decision}

@app.post("/tasks/{task_id}/enqueue")
async def enqueue_task(task_id: str, user=Depends(get_current_user)):
    row = fetch_one("SELECT id, status, title FROM tasks WHERE id=%s AND org_id=%s",
                    (task_id, user["org_id"]))
    if not row:
        raise HTTPException(404, "Task not found")
    if row["status"] != "approved":
        raise HTTPException(403, "Task must be approved before enqueue")
    enqueue({"id": task_id, "code": f"print({row['title']!r})", "org_id": str(user["org_id"])})
    db_execute("UPDATE tasks SET status='queued', updated_at=now() WHERE id=%s", (task_id,))
    return {"task_id": task_id, "status": "queued"}

@app.get("/evidence/{task_id}")
async def get_evidence(task_id: str, user=Depends(get_current_user)):
    rows = fetch_all(
        """SELECT e.kind, e.payload, e.created_at
           FROM evidence e JOIN tasks t ON t.id = e.task_id
           WHERE e.task_id=%s AND t.org_id=%s""",
        (task_id, user["org_id"])
    )
    return {"task_id": task_id, "evidence": rows}
