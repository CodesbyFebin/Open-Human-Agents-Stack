"""Node Pipeline DAG — unit of autonomous work. Fail-closed on error and human review."""
from __future__ import annotations
import asyncio, time, uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

class NodeType(str, Enum):
    RESEARCH_AGENT = "research_agent"
    DURABLE_CODE_AGENT = "durable_code_agent"
    COMFY_RENDER = "comfy_render_node"
    HUMAN_REVIEW_GATE = "human_review_gate"
    STORAGE = "storage"
    CONDITIONAL = "conditional"
    INFERENCE = "inference"
    CODE_AGENT = "code_agent"
    RENDER = "render"
    HUMAN_REVIEW = "human_review"

@dataclass
class PipelineNode:
    id: str
    type: str
    config: dict = field(default_factory=dict)
    status: str = "pending"
    output: Any = None
    error: Optional[str] = None
    inputs: list = field(default_factory=list)
    kind: Any = None

@dataclass
class Pipeline:
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    nodes: Dict[str, PipelineNode] = field(default_factory=dict)
    edges: list = field(default_factory=list)

    def add_node(self, node_id: str, node_type: str, **config) -> PipelineNode:
        node = PipelineNode(id=node_id, type=node_type, config=config)
        self.nodes[node_id] = node
        return node

    def connect(self, src, dst):
        sid = src.id if hasattr(src, "id") else src
        did = dst.id if hasattr(dst, "id") else dst
        self.edges.append((sid, did))
        if did in self.nodes:
            self.nodes[did].inputs.append(sid)

    def topological_sort(self) -> list:
        in_deg = {n: 0 for n in self.nodes}
        adj = {n: [] for n in self.nodes}
        for s, d in self.edges:
            adj[s].append(d)
            in_deg[d] += 1
        q = [n for n, d in in_deg.items() if d == 0]
        order = []
        while q:
            n = q.pop(0)
            order.append(n)
            for m in adj[n]:
                in_deg[m] -= 1
                if in_deg[m] == 0:
                    q.append(m)
        if len(order) != len(self.nodes):
            raise ValueError(f"Cycle detected in pipeline '{self.name}'")
        return order

class NodePipelineGenerator:
    def __init__(self, comfy_executor=None):
        self.comfy = comfy_executor

    def create_pipeline(self, name: str) -> Pipeline:
        return Pipeline(name=name)

    def create_graph(self, name: str, description: str = "") -> Pipeline:
        return Pipeline(name=name)

    def add_node(self, graph, kind, label, config=None):
        nid = f"{getattr(kind, 'value', kind)}-{uuid.uuid4().hex[:6]}"
        return graph.add_node(nid, getattr(kind, 'value', str(kind)), **(config or {}))

    def connect(self, graph, a, b):
        graph.connect(a, b)

    async def execute(self, pipeline, context=None, trajectory_id: str = "") -> dict:
        context = context or {}
        if not hasattr(pipeline, "topological_sort"):
            return {"status": "failed", "error": "invalid pipeline"}
        order = pipeline.topological_sort()
        steps = []
        for nid in order:
            node = pipeline.nodes[nid]
            node.status = "running"
            try:
                out = await self._dispatch(node, context)
                # Fail-closed human review
                if "review" in node.type and out.get("gate") != "approved":
                    node.status = "awaiting_approval"
                    steps.append({"node": nid, "type": node.type, "status": "awaiting_approval"})
                    return {"status": "awaiting_approval", "steps": steps, "graph_id": pipeline.id}
                node.output = out
                node.status = "completed"
                if isinstance(out, dict):
                    context.update(out)
            except Exception as e:
                node.status = "failed"
                node.error = str(e)
                steps.append({"node": nid, "type": node.type, "status": "failed", "error": str(e)})
                return {"status": "failed", "failed_node": nid, "steps": steps, "graph_id": pipeline.id}
            steps.append({"node": nid, "type": node.type, "status": "completed", "output_preview": str(node.output)[:200]})
        return {"status": "completed", "steps": steps, "cost": 0.0, "graph_id": getattr(pipeline, "id", "")}

    async def _dispatch(self, node, ctx):
        t = node.type
        await asyncio.sleep(0.01)
        if "research" in t or t == "inference":
            return {"research_brief": f"Analysis: {ctx.get('prompt','')[:80]}", "confidence": 0.8}
        if "code" in t:
            return {"code_generated": True, "diff_preview": "# stub\n"}
        if "render" in t:
            return {"render_id": "scaffold", "status": "queued"}
        if "review" in t:
            return {"gate": "pending", "reviewer": "human", "blocked": True}
        if "storage" in t or "store" in t:
            return {"stored": True}
        return {"passthrough": t}

def build_example_agent_swarm_pipeline(gen: NodePipelineGenerator):
    p = gen.create_pipeline("agent_swarm_v1")
    r = p.add_node("research", "research_agent")
    c = p.add_node("code", "durable_code_agent")
    rev = p.add_node("review", "human_review_gate")
    v = p.add_node("vault", "storage")
    p.connect(r, c)
    p.connect(c, rev)
    p.connect(rev, v)
    return p
