from julep.projection import SpanData
from julep.execution.langfuse import build_tree, span_id_for

def _s(cid, parents=()):
    return SpanData(name=cid, cid=cid, node=cid, start_ts=0.0, end_ts=1.0,
                    status="ok", parents=tuple(parents))

def test_single_root_and_primary_parent():
    spans = [_s("a"), _s("b", ["a"]), _s("c", ["a", "b"])]
    nodes = build_tree(spans, run_id="r")
    roots = [n for n in nodes if n.is_root]
    assert len(roots) == 1
    by_cid = {n.span.cid: n for n in nodes if n.span is not None}
    assert by_cid["a"].parent_id == roots[0].span_id        # no cause -> root
    assert by_cid["b"].parent_id == span_id_for("a")        # primary = first cause
    assert by_cid["c"].parent_id == span_id_for("a")        # first cause
    assert span_id_for("b") in by_cid["c"].link_ids         # extra cause -> link

def test_cycle_falls_back_to_root():
    spans = [_s("x", ["y"]), _s("y", ["x"])]
    nodes = build_tree(spans, run_id="r")
    # neither x nor y may list the other as an ancestor chain that loops; both resolve
    assert all(n.parent_id is not None for n in nodes if not n.is_root)
