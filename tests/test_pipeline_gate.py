import asyncio
import pytest
from backend.pipeline.node_pipeline import NodePipelineGenerator

def test_human_review_blocks_downstream_storage():
    gen = NodePipelineGenerator()
    graph = gen.create_pipeline("approval-gate")
    first = graph.add_node("research", "research_agent")
    review = graph.add_node("review", "human_review_gate")
    store = graph.add_node("store", "storage")
    graph.connect(first, review)
    graph.connect(review, store)
    result = asyncio.run(gen.execute(graph, {}))
    assert result["status"] == "awaiting_approval"
    assert review.status == "awaiting_approval"
    assert store.status == "pending"

def test_cycle_is_rejected():
    gen = NodePipelineGenerator()
    graph = gen.create_pipeline("cycle")
    a = graph.add_node("a", "research_agent")
    b = graph.add_node("b", "storage")
    graph.connect(a, b)
    graph.connect(b, a)
    with pytest.raises(ValueError, match="Cycle detected"):
        asyncio.run(gen.execute(graph, {}))
