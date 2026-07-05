from julep.execution.langfuse import export_run_to_langfuse
from julep.projection import ProjectionEvent, EventType

def _planned(node, cid, eid, causes=()):
    return ProjectionEvent(event_id=eid, type=EventType.PLANNED, node=node, cid=cid, ts=0.0, causes=causes)
def _did(node, cid, eid, causes=(), attrs=None, cost=None):
    return ProjectionEvent(event_id=eid, type=EventType.DID, node=node, cid=cid, ts=1.0,
                           causes=causes, attrs=attrs or {}, cost=cost)

class _Span:
    def __init__(self, name, ctx):
        self.name = name
        self.ctx = ctx
        self.attrs = {}
        self.ended = False

    def set_attribute(self, k, v):
        self.attrs[k] = v

    def set_status(self, *a, **k):
        pass

    def record_exception(self, *a, **k):
        pass

    def get_span_context(self):
        return self.ctx

    def end(self, end_time=None):
        self.ended = True


class _Tracer:
    def __init__(self):
        self.spans = []

    def start_span(self, name, start_time=None, links=None, context=None):
        s = _Span(name, object())
        s.parent_ctx = context
        s.links = links
        self.spans.append(s)
        return s

def test_export_emits_root_plus_spans():
    events = [
        _planned("reasoner", "c0", "e0"),
        _did("reasoner", "c0", "e1", causes=("e0",),
             attrs={"llm.model": "m", "llm.usage": {"input": 5, "output": 2, "total": 7}}),
    ]
    tr = _Tracer()
    n = export_run_to_langfuse(events, run_id="run-1", tracer=tr, trace_name="t", session_id="s")
    assert n >= 1
    names = [s.name for s in tr.spans]
    assert any("reasoner" in nm for nm in names)
    gen = [s for s in tr.spans if s.attrs.get("langfuse.observation.type") == "generation"]
    assert gen and gen[0].attrs["gen_ai.usage.input_tokens"] == 5
