from julep.projection import InMemoryProjection, ProjectionEmitter
from julep.cli.tracetree import render_tree


def test_renders_parent_child(capsys):
    proj = InMemoryProjection()
    em = ProjectionEmitter(proj)
    root = em.plan("n0", "c0")
    em.did("n0", "c0", value={"x": 1}, cost=1.0, causes=[])
    child = em.plan("n1", "c1", causes=[root])
    em.did("n1", "c1", value={"y": 2}, cost=2.0, causes=[child])
    tree = render_tree(proj.events())
    assert "n0" in tree and "n1" in tree
    assert "└─" in tree or "├─" in tree   # box-drawing tree structure
    assert "ok" in tree                    # status rendered


def test_generation_without_reported_cost_renders_unknown():
    projection = InMemoryProjection()
    emitter = ProjectionEmitter(projection)
    planned = emitter.plan("think", "c0")
    emitter.did(
        "think",
        "c0",
        value="answer",
        causes=[planned],
        attrs={"llm.model": "openai/gpt-test", "llm.usage": {"total": 4}},
    )

    tree = render_tree(projection.events())

    assert "cost=unknown" in tree
    assert "$2.0000" not in tree


def test_generation_preserves_real_zero_cost():
    projection = InMemoryProjection()
    emitter = ProjectionEmitter(projection)
    planned = emitter.plan("think", "c0")
    emitter.did(
        "think",
        "c0",
        value="answer",
        cost=0.0,
        causes=[planned],
        attrs={"llm.model": "local/free"},
    )

    assert "$0.0000" in render_tree(projection.events())
