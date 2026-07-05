"""Observability projection + OTel rendering tests (pure, no Temporal)."""

from __future__ import annotations

from julep.projection import (
    EventType, InMemoryProjection, ProjectionEmitter, ValueStore,
)
from julep.execution.otel import spans_to_dicts


def test_value_store_dedups_identical_values():
    vs = ValueStore()
    r1 = vs.put({"a": 1})
    r2 = vs.put({"a": 1})
    r3 = vs.put({"a": 2})
    assert r1 == r2 and r1 != r3
    assert vs.get(r1) == {"a": 1}


def test_emitter_ids_are_deterministic_logical_clock():
    s1 = InMemoryProjection()
    e1 = ProjectionEmitter(s1)
    s2 = InMemoryProjection()
    e2 = ProjectionEmitter(s2)
    ids1 = [e1.plan("n", "c0"), e1.did("n", "c0", value=1)]
    ids2 = [e2.plan("n", "c0"), e2.did("n", "c0", value=1)]
    assert ids1 == ids2  # no wall clock; replay-stable


def test_planned_then_did_resolves_status_and_clears_pending():
    store = InMemoryProjection()
    em = ProjectionEmitter(store)
    em.plan("root", "c0", shape="Pipeline")
    assert store.pending() == ["c0"]
    em.did("root", "c0", value=7, cost=1.0, shape="Pipeline")
    assert store.status_by_activation()["c0"] == EventType.DID
    assert store.pending() == []


def test_failure_recorded():
    store = InMemoryProjection()
    em = ProjectionEmitter(store)
    em.plan("leaf", "c1", shape="Pipeline")
    em.fail("leaf", "c1", "boom")
    fails = store.failures()
    assert len(fails) == 1 and fails[0].error == "boom"


def test_cost_rolls_up_by_shape():
    store = InMemoryProjection()
    em = ProjectionEmitter(store)
    em.did("a", "c0", value=1, cost=2.0, shape="Pipeline")
    em.did("b", "c1", value=1, cost=3.0, shape="Pipeline")
    em.did("c", "c2", value=1, cost=5.0, shape="Dataflow")
    rollup = store.cost_by_shape()
    assert rollup["Pipeline"] == 5.0 and rollup["Dataflow"] == 5.0


def test_latest_value_threads_through_value_store():
    store = InMemoryProjection()
    em = ProjectionEmitter(store)
    em.did("node", "c0", value={"v": 99})
    assert store.latest_value("node") == {"v": 99}


def test_spans_carry_status_and_causality():
    store = InMemoryProjection()
    em = ProjectionEmitter(store)
    # Thread the produced event id as the cause of the next activation, the way
    # the interpreter does, so parents resolve back to the producing cid.
    em.plan("root", "c0", shape="Pipeline")
    d0 = em.did("root", "c0", value=1, cost=0.0, shape="Pipeline")
    em.plan("leaf", "c1", causes=(d0,), shape="Pipeline")
    em.fail("leaf", "c1", "kaboom", causes=(d0,))

    spans = {s["cid"]: s for s in spans_to_dicts(store.events())}
    assert spans["c0"]["status"] == "ok"
    assert spans["c1"]["status"] == "error" and spans["c1"]["error"] == "kaboom"
    assert spans["c1"]["parents"] == ["c0"]  # cause event id resolved to producer cid


def test_unfinished_activation_renders_as_open_span():
    store = InMemoryProjection()
    em = ProjectionEmitter(store)
    em.plan("waiting", "c0", shape="Pipeline")  # never completed
    (span,) = [s for s in spans_to_dicts(store.events()) if s["cid"] == "c0"]
    assert span["status"] == "unfinished" and span["endTs"] is None
