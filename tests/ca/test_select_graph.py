# tests/ca/test_select_graph.py
"""Graph-operator (dbt-style) selector tests.

Edge semantics: ``A.calls == [B]`` means "A calls B", so B is UPSTREAM of A
(a dependency/callee) and A is DOWNSTREAM of B (a dependent/caller).

These tests build ``Module``/``Agent`` objects by hand (no discovery) so the
graph is fully under our control.
"""

from composable_agents.ca.model import Agent, Module
from composable_agents.ca.select import select


def names(agents):
    return sorted(a.name for a in agents)


def chain_module() -> Module:
    """3-node chain a -> b -> c (a calls b, b calls c)."""
    a = Agent(name="a", kind="flow", file="pkg/a.py", line=1, tags=["top"], calls=["b"])
    b = Agent(name="b", kind="flow", file="pkg/b.py", line=1, tags=["mid"], calls=["c"])
    c = Agent(name="c", kind="flow", file="pkg/c.py", line=1, tags=["leaf"], calls=[])
    return Module(root="/repo", agents=[a, b, c])


def diamond_module() -> Module:
    """Diamond: a -> b, a -> c, b -> d, c -> d (plus a cycle d -> a)."""
    a = Agent(name="a", kind="flow", file="pkg/a.py", line=1, tags=[], calls=["b", "c"])
    b = Agent(name="b", kind="flow", file="pkg/b.py", line=1, tags=["support"], calls=["d"])
    c = Agent(name="c", kind="flow", file="pkg/c.py", line=1, tags=["support"], calls=["d"])
    d = Agent(name="d", kind="flow", file="pkg/d.py", line=1, tags=[], calls=["a"])  # cycle
    return Module(root="/repo", agents=[a, b, c, d])


# --- upstream (+X) -------------------------------------------------------


def test_plus_prefix_is_upstream_closure():
    m = chain_module()
    assert names(select(m, "+a")) == ["a", "b", "c"]
    assert names(select(m, "+b")) == ["b", "c"]
    assert names(select(m, "+c")) == ["c"]  # leaf has no callees


# --- downstream (X+) -----------------------------------------------------


def test_plus_suffix_is_downstream_closure():
    m = chain_module()
    assert names(select(m, "c+")) == ["a", "b", "c"]
    assert names(select(m, "b+")) == ["a", "b"]
    assert names(select(m, "a+")) == ["a"]  # nothing calls a


# --- both directions (+X+) ----------------------------------------------


def test_plus_both_directions():
    m = chain_module()
    assert names(select(m, "+b+")) == ["a", "b", "c"]
    assert names(select(m, "+a+")) == ["a", "b", "c"]
    assert names(select(m, "+c+")) == ["a", "b", "c"]


# --- depth-bounded upstream (N+X) ---------------------------------------


def test_depth_bounded_upstream():
    m = chain_module()
    assert names(select(m, "1+a")) == ["a", "b"]
    assert names(select(m, "2+a")) == ["a", "b", "c"]
    assert names(select(m, "3+a")) == ["a", "b", "c"]
    assert names(select(m, "0+a")) == ["a"]  # depth 0 => just the node


# --- depth-bounded downstream (X+N) -------------------------------------


def test_depth_bounded_downstream():
    m = chain_module()
    assert names(select(m, "c+1")) == ["b", "c"]
    assert names(select(m, "c+2")) == ["a", "b", "c"]
    assert names(select(m, "c+0")) == ["c"]


# --- bounded both directions (N+X+M) ------------------------------------


def test_depth_bounded_both_directions():
    m = chain_module()
    assert names(select(m, "1+b+1")) == ["a", "b", "c"]
    assert names(select(m, "0+b+0")) == ["b"]


# --- dbt @ operator ------------------------------------------------------


def test_at_operator_chain():
    m = chain_module()
    # @a: a + downstream-closure(a)={a}, then upstream of each => {a,b,c}
    assert names(select(m, "@a")) == ["a", "b", "c"]
    # @c: downstream-closure(c)={a,b,c}; upstream of each adds nothing new
    assert names(select(m, "@c")) == ["a", "b", "c"]
    # @b: downstream(b)={a,b}; upstream of a={b,c}, of b={c} => {a,b,c}
    assert names(select(m, "@b")) == ["a", "b", "c"]


# --- composition with tag: base -----------------------------------------


def test_operator_composes_with_tag_base():
    m = chain_module()
    # +tag:mid => upstream of every agent carrying tag 'mid' (=> b) plus b itself
    assert names(select(m, "+tag:mid")) == ["b", "c"]
    # tag:leaf+ => downstream of leaf-tagged (c) => {a,b,c}
    assert names(select(m, "tag:leaf+")) == ["a", "b", "c"]


def test_operator_composes_with_tag_base_multi_match():
    m = diamond_module()
    # +tag:support => {b,c} + full upstream closure. upstream(b)={d}, upstream(c)={d},
    # upstream(d)={a} (d calls a, the cycle), upstream(a)={b,c}. Closure = all four.
    assert names(select(m, "+tag:support")) == ["a", "b", "c", "d"]


# --- composition with path: base ----------------------------------------


def test_operator_composes_with_path_base():
    m = chain_module()
    assert names(select(m, "+path:pkg/a.py")) == ["a", "b", "c"]


# --- set algebra still composes -----------------------------------------


def test_operator_with_space_union_and_comma_intersection():
    m = chain_module()
    # space = union of comma-groups
    assert names(select(m, "+c +a")) == ["a", "b", "c"]
    assert names(select(m, "c+ a+")) == ["a", "b", "c"]
    # comma = intersection within a group
    assert names(select(m, "+a,+b")) == ["b", "c"]  # {a,b,c} & {b,c}


# --- exclude still composes ---------------------------------------------


def test_operator_with_exclude():
    m = chain_module()
    assert names(select(m, "+a", exclude="c")) == ["a", "b"]
    assert names(select(m, "+a", exclude="+c")) == ["a", "b"]


# --- cycles terminate ----------------------------------------------------


def test_cycles_terminate():
    m = diamond_module()
    # +a => upstream closure of a; with d -> a cycle this must still terminate
    assert names(select(m, "+a")) == ["a", "b", "c", "d"]
    assert names(select(m, "a+")) == ["a", "b", "c", "d"]
    assert names(select(m, "@a")) == ["a", "b", "c", "d"]


# --- multi-match upstream closure (superset-caller cycle) ---------------


def test_upstream_closure_includes_superset_caller_in_cycle():
    """Regression: a node that calls every member of a multi-match start set
    must still appear in the upstream closure when it is reachable upstream
    (via a cycle). Earlier impl wrongly 'blocked' such nodes."""
    a = Agent(name="a", kind="flow", file="pkg/a.py", line=1, tags=["t"], calls=["x"])
    b = Agent(name="b", kind="flow", file="pkg/b.py", line=1, tags=["t"], calls=["x", "y"])
    x = Agent(name="x", kind="flow", file="pkg/x.py", line=1, tags=[], calls=["p"])
    y = Agent(name="y", kind="flow", file="pkg/y.py", line=1, tags=[], calls=[])
    p = Agent(name="p", kind="flow", file="pkg/p.py", line=1, tags=[], calls=["a", "b"])
    m = Module(root="/repo", agents=[a, b, x, y, p])
    # start = tag:t = {a,b}. Upstream: a->x->p, b->{x,y}, p->{a,b} (cycle).
    # Full upstream closure must include p.
    assert names(select(m, "+tag:t")) == ["a", "b", "p", "x", "y"]


# --- unknown base resolves to empty -------------------------------------


def test_unknown_base_is_empty():
    m = chain_module()
    assert names(select(m, "+nope")) == []
    assert names(select(m, "nope+")) == []
    assert names(select(m, "@nope")) == []
    assert names(select(m, "2+nope")) == []


# --- dangling call targets (non-agent callees) are ignored --------------


def test_dangling_call_targets_ignored():
    """calls[] entries that are not real agents must not appear in any closure."""
    a = Agent(name="a", kind="flow", file="pkg/a.py", line=1, tags=[], calls=["b", "ghost"])
    b = Agent(name="b", kind="flow", file="pkg/b.py", line=1, tags=[], calls=["missing"])
    m = Module(root="/repo", agents=[a, b])
    assert names(select(m, "+a")) == ["a", "b"]  # 'ghost'/'missing' never appear
    assert names(select(m, "a+")) == ["a"]  # nothing calls a
    assert names(select(m, "@a")) == ["a", "b"]


# --- @ operator composes with multi-match tag:/path: bases --------------


def test_at_operator_composes_with_tag_base():
    m = diamond_module()
    # @tag:support => start={b,c}; downstream-closure of each (cycle d->a) then
    # full upstream of all => entire reachable graph = {a,b,c,d}.
    assert names(select(m, "@tag:support")) == ["a", "b", "c", "d"]


def test_at_operator_composes_with_path_base():
    m = chain_module()
    # @path:pkg/b.py => base={b}; downstream(b)={a,b}; upstream of a={b,c}, of b={c}
    assert names(select(m, "@path:pkg/b.py")) == ["a", "b", "c"]


# --- regression: bare names + set algebra unchanged ---------------------


def test_bare_names_regression():
    m = chain_module()
    assert names(select(m, "a")) == ["a"]
    assert names(select(m, "a b")) == ["a", "b"]  # union
    assert names(select(m, "tag:top,a")) == ["a"]  # intersection
    assert names(select(m, "")) == ["a", "b", "c"]  # empty => all
