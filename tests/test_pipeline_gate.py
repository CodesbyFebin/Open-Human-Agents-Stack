import asyncio
from backend.pipeline.node_pipeline import NodePipelineGenerator, NodeKind

def run(graph, generator):
    return asyncio.run(generator.execute(graph, {}))

def test_human_review_blocks_downstream_artifact_storage():
    gen = NodePipelineGenerator()
    graph = gen.create_graph("review")
    first = gen.add_node(graph, NodeKind.INFERENCE, "research")
    gate = gen.add_node(graph, NodeKind.HUMAN_REVIEW, "review")
    store = gen.add_node(graph, NodeKind.ARTIFACT_STORE, "storage")
    gen.connect(graph, first.id, gate.id)
    gen.connect(graph, gate.id, store.id)
    result = run(graph, gen)
    assert result["status"] == "awaiting_approval"
    assert result["nodes"][gate.id] == "awaiting_approval"
    assert result["nodes"][store.id] == "idle"
    assert store.id not in result["results"]

def test_cycle_never_reports_success():
    gen = NodePipelineGenerator()
    graph = gen.create_graph("cyclic")
    first = gen.add_node(graph, NodeKind.CONDITION, "a")
    second = gen.add_node(graph, NodeKind.CONDITION, "b")
    gen.connect(graph, first.id, second.id)
    gen.connect(graph, second.id, first.id)
    result = run(graph, gen)
    assert result["status"] == "failed"
    assert all(status == "failed" for status in result["nodes"].values())
