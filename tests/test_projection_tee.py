from __future__ import annotations

from julep.projection import (
    InMemoryProjection,
    ProjectionEmitter,
    ProjectionEvent,
    TeeStore,
)


class _ListSink:
    def __init__(self) -> None:
        self.events: list[ProjectionEvent] = []

    def append(self, event: ProjectionEvent) -> None:
        self.events.append(event)


def test_tee_fans_out_and_queries_primary() -> None:
    primary = InMemoryProjection()
    sink = _ListSink()
    tee = TeeStore(primary, sink)

    emitter = ProjectionEmitter(tee)
    eid = emitter.plan("n1", "n1@1")
    emitter.did("n1", "n1@1", value={"x": 1}, causes=(eid,))

    assert [e.type.value for e in primary.events()] == ["Planned", "Did"]
    assert [e.type.value for e in sink.events] == ["Planned", "Did"]
    assert tee.events() == primary.events()


def test_tee_exposes_primary_value_store() -> None:
    primary = InMemoryProjection()
    tee = TeeStore(primary, _ListSink())
    # ProjectionEmitter discovers the value store via getattr(store, "values").
    assert tee.values is primary.values

    emitter = ProjectionEmitter(tee)
    emitter.did("n1", "n1@1", value={"big": "payload"})
    [did] = [e for e in primary.events() if e.type.value == "Did"]
    assert did.value_ref is not None
    assert primary.values.get(did.value_ref) == {"big": "payload"}
