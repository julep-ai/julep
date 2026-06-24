# tests/ca/test_runcache.py
from composable_agents.ca.runcache import failed_agents, load_run, save_run
from composable_agents.projection import (
    InMemoryProjection,
    ProjectionEmitter,
    ProjectionEvent,
)


def test_save_and_load_roundtrip(tmp_path):
    proj = InMemoryProjection()
    em = ProjectionEmitter(proj)
    em.plan("n0", "c0")
    em.did("n0", "c0", value=1, cost=1.0)
    save_run(str(tmp_path), run_id="r1", agent="triage", status="done", events=proj.events())
    loaded = load_run(str(tmp_path), "r1")
    assert loaded is not None
    assert loaded["run_id"] == "r1"
    assert loaded["agent"] == "triage"
    assert loaded["status"] == "done"
    assert len(loaded["events"]) == 2


def test_loaded_events_rehydrate_to_projection_events(tmp_path):
    proj = InMemoryProjection()
    em = ProjectionEmitter(proj)
    em.plan("n0", "c0")
    em.did("n0", "c0", value={"x": 1}, cost=2.5)
    original = proj.events()
    save_run(str(tmp_path), run_id="r-rt", agent="triage", status="done", events=original)

    loaded = load_run(str(tmp_path), "r-rt")
    assert loaded is not None
    rehydrated = [ProjectionEvent.from_json(e) for e in loaded["events"]]
    assert len(rehydrated) == len(original)
    for got, want in zip(rehydrated, original, strict=True):
        assert got.event_id == want.event_id
        assert got.type == want.type
        assert got.node == want.node
        assert got.cid == want.cid
        assert got.ts == want.ts
        assert got.causes == want.causes
        assert got.value_ref == want.value_ref
        assert got.cost == want.cost


def test_load_run_missing_returns_none(tmp_path):
    assert load_run(str(tmp_path), "does-not-exist") is None


def test_failed_agents_reads_status(tmp_path):
    save_run(str(tmp_path), run_id="r2", agent="escalate", status="error", events=[])
    assert failed_agents(str(tmp_path)) == {"escalate"}


def test_failed_agents_excludes_done_and_ok(tmp_path):
    save_run(str(tmp_path), run_id="ok1", agent="triage", status="done", events=[])
    save_run(str(tmp_path), run_id="ok2", agent="support_bot", status="ok", events=[])
    save_run(str(tmp_path), run_id="bad", agent="escalate", status="error", events=[])
    assert failed_agents(str(tmp_path)) == {"escalate"}


def test_failed_agents_empty_when_no_cache(tmp_path):
    assert failed_agents(str(tmp_path)) == set()
