from composable_agents.projection import ProjectionEvent, EventType, to_otel_spans

def _ev(**kw):
    base = dict(event_id="e0", type=EventType.PLANNED, node="n", cid="c0", ts=0.0)
    base.update(kw)
    return ProjectionEvent(**base)

def test_spandata_carries_attrs_cost_refs():
    planned = _ev(event_id="e0", type=EventType.PLANNED, node="n", cid="c0", ts=0.0)
    did = _ev(event_id="e1", type=EventType.DID, node="n", cid="c0", ts=1.0,
              causes=("e0",), value_ref="val:abc", cost=0.02,
              attrs={"llm.model": "m", "llm.usage": {"input": 1, "output": 2, "total": 3}})
    spans = to_otel_spans([planned, did])
    s = spans[0]
    assert s.cost == 0.02
    assert s.value_ref == "val:abc"
    assert s.attrs["llm.model"] == "m"
    assert s.planned_event_id == "e0"
    assert s.terminal_event_id == "e1"
