# backend/pipeline/node_pipeline.py
# Expanded node-based pipeline generation engine
# Composes ComfyUI graphs, inference fallbacks, mobile vision steps, and durable agent nodes
# into a single executable DAG for multi-human/agent workflows.

import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from .comfy_graph import ComfyGraphExecutor

class NodeKind(str, Enum):
    INFERENCE = "inference"
    RENDER = "render"
    MOBILE_VISION = "mobile_vision"
    CODE_AGENT = "code_agent"
    HUMAN_REVIEW = "human_review"
    SCHEMA_MIGRATE = "schema_migrate"
    ARTIFACT_STORE = "artifact_store"
    CONDITION = "condition"

@dataclass
class PipelineNode:
    id: str
    kind: NodeKind
    label: str
    config: Dict[str, Any] = field(default_factory=dict)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    status: str = "idle"  # idle | queued | running | committed | failed

@dataclass
class PipelineGraph:
    id: str
    name: str
    nodes: Dict[str, PipelineNode] = field(default_factory=dict)
    edges: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class NodePipelineGenerator:
    """Builds and executes multi-stage node graphs that unify rendering, inference, mobile, and agent work."""

    def __init__(self, comfy_executor: Optional[ComfyGraphExecutor] = None):
        self.comfy = comfy_executor
        self._handlers: Dict[NodeKind, Callable] = {
            NodeKind.RENDER: self._exec_render,
            NodeKind.INFERENCE: self._exec_inference,
            NodeKind.MOBILE_VISION: self._exec_mobile,
            NodeKind.CODE_AGENT: self._exec_code_agent,
            NodeKind.HUMAN_REVIEW: self._exec_human_review,
            NodeKind.SCHEMA_MIGRATE: self._exec_schema,
            NodeKind.ARTIFACT_STORE: self._exec_store,
            NodeKind.CONDITION: self._exec_condition,
        }

    def create_graph(self, name: str, description: str = "") -> PipelineGraph:
        return PipelineGraph(
            id=str(uuid.uuid4()),
            name=name,
            metadata={"description": description, "version": "2.0"}
        )

    def add_node(self, graph: PipelineGraph, kind: NodeKind, label: str, config: Optional[Dict[str, Any]] = None) -> PipelineNode:
        node = PipelineNode(
            id=f"{kind.value}-{uuid.uuid4().hex[:8]}",
            kind=kind,
            label=label,
            config=config or {}
        )
        graph.nodes[node.id] = node
        return node

    def connect(self, graph: PipelineGraph, from_id: str, to_id: str, output_key: str = "default", input_key: str = "default"):
        graph.edges.append({"from": from_id, "to": to_id, "output": output_key, "input": input_key})
        if to_id in graph.nodes and from_id not in graph.nodes[to_id].inputs:
            graph.nodes[to_id].inputs.append(from_id)
        if from_id in graph.nodes and to_id not in graph.nodes[from_id].outputs:
            graph.nodes[from_id].outputs.append(to_id)

    def to_comfy_subgraph(self, graph: PipelineGraph, render_node_id: str, prompt: str, seed: int = 42) -> Dict[str, Any]:
        """Convert a render node into a full ComfyUI prompt graph."""
        if not self.comfy:
            raise RuntimeError("ComfyGraphExecutor not configured")
        return self.comfy.evaluate_generation_primitives(prompt, seed)

    async def execute(self, graph: PipelineGraph, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Topological execution of the pipeline (simple Kahn-style)."""
        context = context or {}
        results: Dict[str, Any] = {}
        pending = set(graph.nodes.keys())
        completed = set()

        while pending:
            ready = [
                nid for nid in pending
                if all(inp in completed for inp in graph.nodes[nid].inputs)
            ]
            if not ready:
                break  # cycle or missing deps
            for nid in ready:
                node = graph.nodes[nid]
                node.status = "running"
                handler = self._handlers.get(node.kind, self._exec_passthrough)
                try:
                    result = await handler(node, results, context)
                    results[nid] = result
                    # Human review gate blocks dependents until approved
                    if node.kind == NodeKind.HUMAN_REVIEW and result.get("gate") != "approved":
                        node.status = "awaiting_approval"
                        # Do not mark completed — dependents stay blocked
                        pending.remove(nid)
                        continue
                    node.status = "committed"
                except Exception as e:
                    node.status = "failed"
                    results[nid] = {"error": str(e)}
                    # Failure stops dependents: do not add to completed
                    pending.remove(nid)
                    continue
                completed.add(nid)
                pending.remove(nid)
        failed = any(n.status == "failed" for n in graph.nodes.values())
        awaiting = any(n.status == "awaiting_approval" for n in graph.nodes.values())
        status = "failed" if failed else ("awaiting_approval" if awaiting else "executed")
        return {"graph_id": graph.id, "status": status, "results": results, "nodes": {k: v.status for k, v in graph.nodes.items()}}

    # --- Node handlers ---
    async def _exec_render(self, node: PipelineNode, results: Dict, ctx: Dict) -> Dict:
        prompt = node.config.get("prompt") or ctx.get("prompt", "cinematic agent swarm")
        if self.comfy:
            graph_json = self.comfy.evaluate_generation_primitives(prompt)
            prompt_id = self.comfy.queue_node_graph(graph_json, node.id)
            return {"prompt_id": prompt_id, "graph": graph_json}
        return {"status": "render_stub", "prompt": prompt}

    async def _exec_inference(self, node: PipelineNode, results: Dict, ctx: Dict) -> Dict:
        return {"model": node.config.get("model", "local-fallback"), "tokens": 0, "output": "inference stub"}

    async def _exec_mobile(self, node: PipelineNode, results: Dict, ctx: Dict) -> Dict:
        return {"device": node.config.get("device_id", "emulator-5554"), "bounds": [0, 0, 1000, 1000], "tap": True}

    async def _exec_code_agent(self, node: PipelineNode, results: Dict, ctx: Dict) -> Dict:
        return {"agent": node.config.get("agent", "pydantic-ai"), "diff": "+++ stub patch", "files_changed": 1}

    async def _exec_human_review(self, node: PipelineNode, results: Dict, ctx: Dict) -> Dict:
        return {"reviewer": "human", "gate": "pending", "diff_id": node.id, "blocked": True}

    async def _exec_schema(self, node: PipelineNode, results: Dict, ctx: Dict) -> Dict:
        return {"version": node.config.get("version", "v1"), "fingerprint": "sha256-stub"}

    async def _exec_store(self, node: PipelineNode, results: Dict, ctx: Dict) -> Dict:
        return {"bucket": node.config.get("bucket", "artifacts"), "file_id": str(uuid.uuid4())}

    async def _exec_condition(self, node: PipelineNode, results: Dict, ctx: Dict) -> Dict:
        return {"branch": node.config.get("default_branch", "continue")}

    async def _exec_passthrough(self, node: PipelineNode, results: Dict, ctx: Dict) -> Dict:
        return {"passthrough": node.kind.value}

def build_example_agent_swarm_pipeline(generator: NodePipelineGenerator) -> PipelineGraph:
    """Example: research → code agent → render evidence → human review → store."""
    g = generator.create_graph("Agent Swarm Evidence Pipeline", "Multi-human/agent research-to-evidence flow")
    research = generator.add_node(g, NodeKind.INFERENCE, "Research Swarm", {"model": "local-orca"})
    code = generator.add_node(g, NodeKind.CODE_AGENT, "Durable Coder", {"agent": "pydantic-ai"})
    render = generator.add_node(g, NodeKind.RENDER, "Evidence Visualizer", {"prompt": "terminal evidence console"})
    review = generator.add_node(g, NodeKind.HUMAN_REVIEW, "Clearance Gate")
    store = generator.add_node(g, NodeKind.ARTIFACT_STORE, "Appwrite Vault", {"bucket": "evidence"})
    generator.connect(g, research.id, code.id)
    generator.connect(g, code.id, render.id)
    generator.connect(g, render.id, review.id)
    generator.connect(g, review.id, store.id)
    return g
