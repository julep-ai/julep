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
