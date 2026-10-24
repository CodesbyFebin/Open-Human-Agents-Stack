import asyncio
from backend.pipeline.node_pipeline import NodePipelineGenerator, NodeKind

def test_human_review_blocks():
    gen = NodePipelineGenerator()
    g = gen.create_graph("t")
    a = gen.add_node(g, NodeKind.INFERENCE, "a")
    b = gen.add_node(g, NodeKind.HUMAN_REVIEW, "gate")
    gen.connect(g, a.id, b.id)
    result = asyncio.get_event_loop().run_until_complete(gen.execute(g, {}))
    assert result["status"] in ("awaiting_approval", "failed", "executed")
