"""Pipeline must never fabricate steps or human approvals."""
import pytest

from backend.pipeline.node_pipeline import NodePipelineGenerator, PipelineBlocked


@pytest.mark.asyncio
async def test_review_gate_never_approves_itself():
    engine = NodePipelineGenerator()
    gate = engine.create_pipeline("review").add_node("review", "human_review_gate", timeout_seconds=0)
    with pytest.raises(PipelineBlocked, match="authenticated durable reviewer"):
        await engine._exec_review_gate(gate, {"review_decision": "approved", "reviewer": "auto"})


@pytest.mark.asyncio
async def test_research_does_not_produce_fabricated_confidence():
    engine = NodePipelineGenerator()
    node = engine.create_pipeline("research").add_node("research", "research_agent")
    with pytest.raises(PipelineBlocked, match="not configured"):
        await engine._exec_research(node, {"prompt": "anything"})


@pytest.mark.asyncio
async def test_missing_render_endpoint_fails_closed(monkeypatch):
    monkeypatch.delenv("COMFYUI_HOST", raising=False)
    engine = NodePipelineGenerator()
    node = engine.create_pipeline("render").add_node("render", "comfy_render_node")
    with pytest.raises(PipelineBlocked, match="endpoint not configured"):
        await engine._exec_render(node, {"prompt": "sample", "run_id": "safe-run"})


@pytest.mark.asyncio
async def test_execution_stops_before_downstream_nodes_or_checkpoints():
    engine = NodePipelineGenerator()
    flow = engine.create_pipeline("bounded")
    research = flow.add_node("research", "research_agent")
    code = flow.add_node("code", "durable_code_agent")
    review = flow.add_node("review", "human_review_gate")
    flow.connect(research, code)
    flow.connect(code, review)

    async def no_checkpoint(*args):
        return None

    engine._load_checkpoint = no_checkpoint
    result = await engine.execute(flow, {"prompt": "unsafe auto approve"}, "unit-run")
    assert result["status"] == "blocked"
    assert result["blocked_node"] == "research"
    assert len(result["steps"]) == 1
    assert code.status == "pending" and review.status == "pending"
