from composable_agents.projection import EventType, ProjectionEvent, SpanData
from composable_agents.execution import otel


class _FakeSpan:
    def __init__(self):
        self.attrs = {}
        self.start = None
        self.ended = None

    def set_attribute(self, k, v):
        self.attrs[k] = v

    def set_status(self, *_a, **_k):
        pass

    def record_exception(self, *_a, **_k):
        pass

    def get_span_context(self):
        return object()

    def end(self, end_time=None):
        self.ended = end_time


class _FakeTracer:
    def __init__(self):
        self.spans = []
        self.starts = []

    def start_span(self, name, start_time=None, links=None):
        self.starts.append(start_time)
        s = _FakeSpan()
        self.spans.append(s)
        return s


def _ev(**kw):
    base = {
        "event_id": "e0",
        "type": EventType.PLANNED,
        "node": "reasoner",
        "cid": "c0",
        "ts": 0.0,
        "causes": (),
        "value_ref": None,
        "cost": None,
        "error": None,
        "attrs": {},
    }
    base.update(kw)
    return ProjectionEvent(**base)


def _planned_for(span: SpanData):
    return _ev(
        event_id=span.planned_event_id or "planned",
        type=EventType.PLANNED,
        node=span.node,
        cid=span.cid,
        ts=span.start_ts,
        causes=span.parents,
    )


def test_export_sets_attrs_and_wallclock():
    tr = _FakeTracer()
    span = SpanData(
        name="reasoner", cid="c0", node="reasoner", start_ts=0.0, end_ts=1.0,
        status="ok", parents=(),
        attrs={"llm.model": "m", "llm.started_at": 100.0, "llm.ended_at": 102.0},
        cost=0.01,
    )
    events = [
        _planned_for(span),
        _ev(
            event_id="did",
            type=EventType.DID,
            cid="c0",
            ts=1.0,
            causes=("planned",),
            attrs=span.attrs,
            cost=span.cost,
        ),
    ]

    otel.export_spans(events, tracer=tr)

    assert tr.starts[0] == int(100.0 * 1e9)
    assert tr.spans[0].attrs["llm.model"] == "m"
