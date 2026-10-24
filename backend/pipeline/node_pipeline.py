"""Node Pipeline DAG with PostgreSQL checkpointing."""
from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

import structlog
from sqlalchemy import text

from backend.db import async_session

log = structlog.get_logger()


class NodeType(str, Enum):
    RESEARCH_AGENT = "research_agent"
    DURABLE_CODE_AGENT = "durable_code_agent"
    COMFY_RENDER = "comfy_render_node"
    HUMAN_REVIEW_GATE = "human_review_gate"
    STORAGE = "storage"
    CONDITIONAL = "conditional"


@dataclass
class PipelineNode:
    id: str
    type: NodeType
    config: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    output: Any = None
    error: str | None = None
    started_at: float | None = None
    completed_at: float | None = None


@dataclass
class Pipeline:
    name: str
    nodes: dict[str, PipelineNode] = field(default_factory=dict)
    edges: list[tuple[str, str]] = field(default_factory=list)

    def add_node(self, node_id: str, node_type: str, **config) -> PipelineNode:
        node = PipelineNode(id=node_id, type=NodeType(node_type), config=config)
        self.nodes[node_id] = node
        return node

    def connect(self, from_node: PipelineNode, to_node: PipelineNode):
        self.edges.append((from_node.id, to_node.id))

    def topological_sort(self) -> list[str]:
        in_degree = {n.id: 0 for n in self.nodes.values()}
        adj: dict[str, list[str]] = {n.id: [] for n in self.nodes.values()}
        for src, dst in self.edges:
            adj[src].append(dst)
            in_degree[dst] += 1
        queue = [n for n, d in in_degree.items() if d == 0]
        order = []
        while queue:
            node = queue.pop(0)
            order.append(node)
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        if len(order) != len(self.nodes):
            raise ValueError(f"Cycle detected in pipeline '{self.name}'")
        return order


class NodePipelineGenerator:
    """Constructs and executes DAG pipelines with durable checkpoints."""

    def __init__(self):
        self._executors: dict[NodeType, Callable] = {
            NodeType.RESEARCH_AGENT: self._exec_research,
            NodeType.DURABLE_CODE_AGENT: self._exec_code,
            NodeType.COMFY_RENDER: self._exec_render,
            NodeType.HUMAN_REVIEW_GATE: self._exec_review_gate,
            NodeType.STORAGE: self._exec_storage,
            NodeType.CONDITIONAL: self._exec_conditional,
        }

    def create_pipeline(self, name: str) -> Pipeline:
        return Pipeline(name=name)

    async def execute(self, pipeline: Pipeline, context: dict[str, Any], run_id: str) -> dict[str, Any]:
        order = pipeline.topological_sort()
        steps: list[dict] = []

        for i, node_id in enumerate(order):
            node = pipeline.nodes[node_id]

            # Check for existing checkpoint (resume)
            checkpoint = await self._load_checkpoint(run_id, i, node_id)
            if checkpoint:
                node.output = checkpoint
                node.status = "completed"
                steps.append({"node": node_id, "type": node.type.value, "status": "resumed_from_checkpoint"})
                continue

            node.status = "running"
            node.started_at = time.time()

            try:
                executor = self._executors[node.type]
                node.output = await executor(node, context)
                node.status = "completed"

                # Checkpoint
                await self._save_checkpoint(run_id, i, node_id, node.output)

                if isinstance(node.output, dict):
                    context.update(node.output)

            except Exception as e:
                node.status = "failed"
                node.error = str(e)
                steps.append({"node": node_id, "type": node.type.value, "status": "failed", "error": str(e)})
                return {"status": "failed", "failed_node": node_id, "steps": steps}

            node.completed_at = time.time()
            steps.append({
                "node": node_id, "type": node.type.value,
                "status": node.status,
                "duration_ms": int((node.completed_at - node.started_at) * 1000),
            })

        return {"status": "completed", "steps": steps}

    # ─── Checkpointing ──────────────────────────────────────────────────────

    async def _save_checkpoint(self, run_id: str, step_index: int, step_name: str, output: Any):
        output_json = json.dumps(output) if output else "{}"
        input_hash = hashlib.sha256(output_json.encode()).hexdigest()[:32]
        async with async_session() as s:
            await s.execute(
                text("INSERT INTO checkpoints (run_id, step_index, step_name, input_hash, output) "
                     "VALUES (:r, :i, :n, :h, :o) ON CONFLICT (run_id, step_index) DO UPDATE SET output=:o"),
                {"r": run_id, "i": step_index, "n": step_name, "h": input_hash, "o": output_json},
            )
            await s.commit()

    async def _load_checkpoint(self, run_id: str, step_index: int, step_name: str) -> Any | None:
        async with async_session() as s:
            row = await s.execute(
                text("SELECT output FROM checkpoints WHERE run_id=:r AND step_index=:i AND step_name=:n"),
                {"r": run_id, "i": step_index, "n": step_name},
            )
            result = row.first()
            if result:
                return json.loads(result[0])
        return None

    # ─── Node Executors ─────────────────────────────────────────────────────

    async def _exec_research(self, node: PipelineNode, context: dict) -> dict:
        prompt = context.get("prompt", "")
        await asyncio.sleep(0.05)
        return {"research_brief": f"Analysis for: {prompt[:100]}", "confidence": 0.85}

    async def _exec_code(self, node: PipelineNode, context: dict) -> dict:
        prompt = context.get("prompt", "")
        await asyncio.sleep(0.05)
        return {"code_generated": True, "diff_preview": f"# Generated for: {prompt[:50]}\n"}

    async def _exec_render(self, node: PipelineNode, context: dict) -> dict:
        import os
        comfy_url = os.getenv("COMFYUI_URL", "http://localhost:8188")
        await asyncio.sleep(0.05)
        return {"render_id": "placeholder", "comfy_url": comfy_url, "status": "queued"}

    async def _exec_review_gate(self, node: PipelineNode, context: dict) -> dict:
        timeout = node.config.get("timeout_seconds", 0)
        if timeout == 0:
            # Auto-approve (scaffold mode only — in production, this waits for webhook)
            return {"review_decision": "approved", "reviewer": "auto"}
        # In production: publish to Redis, wait for review_decision event
        return {"review_decision": "approved", "reviewer": "timeout_fallback"}

    async def _exec_storage(self, node: PipelineNode, context: dict) -> dict:
        return {"stored": True, "artifact_count": len(context)}

    async def _exec_conditional(self, node: PipelineNode, context: dict) -> dict:
        threshold = node.config.get("threshold", 0.7)
        score = context.get("confidence", 0.0)
        return {"branch": "pass" if score >= threshold else "fail", "score": score}
