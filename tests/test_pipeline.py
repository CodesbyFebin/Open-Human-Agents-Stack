import pytest
from backend.pipeline.node_pipeline import NodePipelineGenerator

@pytest.fixture
def gen():
    return NodePipelineGenerator()

@pytest.mark.asyncio
async def test_topo_linear(gen):
    p = gen.create_pipeline("linear")
    a = p.add_node("a", "research_agent")
    b = p.add_node("b", "storage")
    p.connect(a, b)
    assert p.topological_sort() == ["a", "b"]

@pytest.mark.asyncio
async def test_cycle(gen):
    p = gen.create_pipeline("c")
    a = p.add_node("a", "research_agent")
    b = p.add_node("b", "storage")
    p.connect(a, b)
    p.connect(b, a)
    with pytest.raises(ValueError):
        p.topological_sort()

@pytest.mark.asyncio
async def test_review_blocks(gen):
    p = gen.create_pipeline("gate")
    a = p.add_node("a", "research_agent")
    b = p.add_node("b", "human_review_gate")
    p.connect(a, b)
    result = await gen.execute(p, {"prompt": "x"}, "t1")
    assert result["status"] == "awaiting_approval"
