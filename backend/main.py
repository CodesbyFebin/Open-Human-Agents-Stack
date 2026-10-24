"""
OpenMinds Control Plane — FastAPI entry
Wires durable agents, node pipelines, telemetry, and mesh services.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
import logging

log = logging.getLogger("openminds")
app = FastAPI(title="OpenMinds Control Plane", version="2.1.0")

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
    return {"status": "operational", "service": "openminds-control-plane", "version": "2.1.0"}

@app.post("/pipeline/run")
async def run_pipeline(req: PipelineRequest):
    try:
        from backend.pipeline.node_pipeline import NodePipelineGenerator, build_example_agent_swarm_pipeline
        from backend.pipeline.comfy_graph import ComfyGraphExecutor
        generator = NodePipelineGenerator(ComfyGraphExecutor("localhost:8188"))
        graph = build_example_agent_swarm_pipeline(generator)
        result = await generator.execute(graph, {"prompt": req.prompt})
        return {"graph_id": getattr(graph, "id", str(uuid.uuid4())), "status": "executed", "result": result}
    except Exception as e:
        log.exception("pipeline execution failed")
        raise HTTPException(status_code=503, detail=f"Pipeline engine unavailable: {e}")

@app.post("/agent/code")
async def run_code_agent(task: AgentTask):
    # Real dispatch requires auth + isolated worker (P0 remaining work).
    # Currently records intent and returns a tracked task id.
    return {
        "task_id": str(uuid.uuid4()),
        "status": "accepted_pending_worker",
        "agent": "durable_coder",
        "message": "Task recorded. Isolated worker dispatch is the next P0 item.",
        "workspace": task.workspace,
        "note": "Authentication and sandbox enforcement required before live execution."
    }

@app.get("/telemetry/summary")
def telemetry_summary():
    # Placeholder until telemetry_pipeline is wired to live queries.
    return {
        "active_runners": 0,
        "circuit_status": "unknown",
        "cost_usd_today": 0.0,
        "trajectories": 0,
        "note": "Live aggregation pending telemetry_pipeline wiring"
    }
