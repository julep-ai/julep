"""Pure interpreter control-flow tests (InMemoryEnv, no Temporal)."""

from __future__ import annotations

import pytest

from julep import (
    Ann, ContextScope,
    arr, call, mcp, think, seq, par, alt, iter_up_to, stage, app,
    sub, race, quorum, human_gate, Contract, freeze, register_pure,
    HAVE_TEMPORAL,
)
from julep.errors import CapabilityDenied
from julep.execution.interpreter import InMemoryEnv, _retry_backoff_for_call, interpret
if HAVE_TEMPORAL:
    from julep.execution.harness import ExecutionPolicy, _TemporalEnv
from julep.projection import EventType, InMemoryProjection, ProjectionEmitter
from conftest import mixed_snapshot, read_snapshot, run


def _env_and_store(flow, **kw):
    fr = freeze(flow, read_snapshot("inc", "double", "half", "a", "b", "c", "other"))
    store = InMemoryProjection()
    return fr, InMemoryEnv(fr.manifest, ProjectionEmitter(store), **kw), store


def _env(flow, **kw):
    fr, env, _store = _env_and_store(flow, **kw)
    return fr, env


TOOLS = {
    "srv/inc": lambda v: v + 1,
    "srv/double": lambda v: v * 2,
    "srv/half": lambda v: v // 2,
    "srv/a": lambda v: ("a", v),
    "srv/b": lambda v: ("b", v),
    "srv/c": lambda v: ("c", v),
}


def test_pipeline_threads_value():
    flow = seq(call(mcp("srv", "inc")), call(mcp("srv", "double")))
    fr, env = _env(flow, tools=TOOLS)
    out = run(interpret(fr.flow, 5, env))
    assert out.value == 12  # (5+1)*2


def test_retryable_call_retries_to_success_with_backoff_sleeps():
    attempts = 0
    sleeps = []

    def flaky(value):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError(f"transient {attempts}")
        return {"ok": value, "attempts": attempts}

    async def sleeper(seconds):
        sleeps.append(seconds)

    flow = call(
        mcp("srv", "inc"),
        ann=Ann(max_attempts=3, retry_interval_s=0.5, backoff_rate=2.0),
    )
    fr, env = _env(flow, tools={"srv/inc": flaky}, sleeper=sleeper)

    out = run(interpret(fr.flow, "x", env))

    assert out.value == {"ok": "x", "attempts": 3}
    assert attempts == 3
    assert sleeps == [0.5, 1.0]


def test_interpreter_retry_backoff_clamps_ann_to_legal_floor():
    node = call(mcp("srv", "inc"), ann=Ann(backoff_rate=0.5))

    assert _retry_backoff_for_call(node) == 1.0


def test_non_retryable_contract_ignores_ann_retry_policy():
    attempts = 0

    def always_fails(value):
        nonlocal attempts
        attempts += 1
        raise RuntimeError(f"no retry for {value}")

    flow = call(
        mcp("srv", "writer"),
        ann=Ann(max_attempts=3, retry_interval_s=0.01, backoff_rate=2.0),
    )
    fr = freeze(flow, mixed_snapshot())
    env = InMemoryEnv(
        fr.manifest,
        ProjectionEmitter(InMemoryProjection()),
        tools={"srv/writer": always_fails},
    )

    with pytest.raises(RuntimeError, match="no retry"):
        run(interpret(fr.flow, "x", env))

    assert attempts == 1


def test_policy_error_does_not_consume_retry_attempts_or_sleep():
    attempts = 0
    sleeps = []

    def denied(value):
        nonlocal attempts
        attempts += 1
        raise CapabilityDenied(f"denied {value}")

    async def sleeper(seconds):
        sleeps.append(seconds)

    flow = call(
        mcp("srv", "inc"),
        ann=Ann(max_attempts=3, retry_interval_s=0.01, backoff_rate=2.0),
    )
    fr, env = _env(flow, tools={"srv/inc": denied}, sleeper=sleeper)

    with pytest.raises(CapabilityDenied, match="denied"):
        run(interpret(fr.flow, "x", env))

    assert attempts == 1
    assert sleeps == []


def test_parallel_collects_branches():
    flow = par(call(mcp("srv", "a")), call(mcp("srv", "b")))
    fr, env = _env(flow, tools=TOOLS)
    out = run(interpret(fr.flow, 9, env))
    assert out.value == [("a", 9), ("b", 9)]


class RecordingEnv(InMemoryEnv):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = []
        self.gather_calls = 0

    async def invoke_reasoner(self, reasoner, value, cid, timeout_s, batchable=False):
        self.events.append("reasoner:start")
        self.events.append("reasoner:end")
        return ("reasoner", value)

    async def run_call(self, node, value, cid):
        self.events.append("tool:start")
        self.events.append("tool:end")
        return ("tool", value)

    async def gather(self, coros):
        self.gather_calls += 1
        self.events.append("gather")
        return await super().gather(coros)


def test_parallel_degrades_to_sequential_when_branch_reads_whole_session():
    flow = par(
        think("ctx_reader", ctx=ContextScope.WHOLE_SESSION),
        call(mcp("srv", "other")),
    )
    fr = freeze(flow, read_snapshot("other"))
    store = InMemoryProjection()
    env = RecordingEnv(fr.manifest, ProjectionEmitter(store))

    out = run(interpret(fr.flow, 7, env))

    assert out.value == [("reasoner", 7), ("tool", 7)]
    assert env.gather_calls == 0
    assert env.events == ["reasoner:start", "reasoner:end", "tool:start", "tool:end"]
    par_did = next(e for e in store.events() if e.node == fr.flow.id and e.type == EventType.DID)
    assert par_did.attrs == {"merge": "degraded", "reason": "whole_session"}


def test_parallel_without_whole_session_still_fans_out():
    flow = par(think("local_reader"), call(mcp("srv", "other")))
    fr = freeze(flow, read_snapshot("other"))
    store = InMemoryProjection()
    env = RecordingEnv(fr.manifest, ProjectionEmitter(store))

    run(interpret(fr.flow, 7, env))

    assert env.gather_calls == 1


def test_race_emits_scheduling_attrs():
    flow = race(call(mcp("srv", "a")), call(mcp("srv", "b")))
    fr, env, store = _env_and_store(flow, tools=TOOLS)

    out = run(interpret(fr.flow, 1, env))

    assert out.value == ("a", 1)
    race_did = next(e for e in store.events() if e.node == fr.flow.id and e.type == EventType.DID)
    assert race_did.attrs == {"merge": "race", "winner": 0, "cancelled": [1]}


def test_real_run_cost_rolls_up_from_annotations():
    flow = seq(
        call(mcp("srv", "a"), ann=Ann(cost=0.25)),
        think("summarizer", ann=Ann(cost=0.75)),
    )
    fr, env, store = _env_and_store(flow, tools=TOOLS, reasoners={"summarizer": lambda v: v})

    run(interpret(fr.flow, 1, env))

    assert store.cost_by_shape()["Pipeline"] == pytest.approx(1.0)


def test_reasoner_reported_cost_metadata_overrides_default():
    flow = think("metered")
    fr, env, store = _env_and_store(
        flow,
        reasoners={"metered": lambda v: {"output": v, "usage": {"costUsd": 0.33}}},
    )

    run(interpret(fr.flow, "doc", env))

    assert store.cost_by_shape()["Pipeline"] == pytest.approx(0.33)


def test_alt_routes_by_pure_predicate():
    register_pure("is_even", lambda v: v % 2 == 0)
    flow = alt("is_even", call(mcp("srv", "half")), call(mcp("srv", "inc")))
    fr, env = _env(flow, tools=TOOLS)
    assert run(interpret(fr.flow, 8, env)).value == 4   # even -> half
    fr2, env2 = _env(flow, tools=TOOLS)
    assert run(interpret(fr2.flow, 7, env2)).value == 8  # odd -> inc


def test_arr_static_args_call_pure_with_kwargs():
    register_pure(
        "static_args.interpret.kwargs",
        lambda value, *, scale, offset: value * scale + offset,
    )
    flow = arr("static_args.interpret.kwargs", args={"scale": 2, "offset": 3})
    store = InMemoryProjection()
    env = InMemoryEnv({}, ProjectionEmitter(store))

    out = run(interpret(flow, 10, env))

    assert out.value == 23


def test_arr_without_static_args_calls_pure_without_kwargs():
    register_pure("static_args.interpret.absent", lambda value: value + 1)
    flow = arr("static_args.interpret.absent")
    store = InMemoryProjection()
    env = InMemoryEnv({}, ProjectionEmitter(store))

    out = run(interpret(flow, 10, env))

    assert out.value == 11


def test_arr_static_args_kwarg_mismatch_surfaces_type_error():
    register_pure("static_args.interpret.mismatch", lambda value: value)
    flow = arr("static_args.interpret.mismatch", args={"unexpected": True})
    store = InMemoryProjection()
    env = InMemoryEnv({}, ProjectionEmitter(store))

    with pytest.raises(TypeError, match="unexpected"):
        run(interpret(flow, 10, env))


def test_iter_up_to_runs_bound_times_and_converges():
    register_pure("at_least_10", lambda v: v >= 10)
    # No convergence: runs exactly bound times.
    flow = iter_up_to(3, call(mcp("srv", "inc")))
    fr, env = _env(flow, tools=TOOLS)
    assert run(interpret(fr.flow, 5, env)).value == 8  # 5 -> 6 -> 7 -> 8
    # With convergence: stops early once predicate holds.
    flow2 = iter_up_to(100, call(mcp("srv", "inc")), until="at_least_10")
    fr2, env2 = _env(flow2, tools=TOOLS)
    assert run(interpret(fr2.flow, 7, env2)).value == 10  # stops at 10


def test_race_picks_first_branch_with_sync_fakes():
    flow = race(call(mcp("srv", "a")), call(mcp("srv", "b")))
    fr, env = _env(flow, tools=TOOLS)
    out = run(interpret(fr.flow, 1, env))
    assert out.value == ("a", 1)  # branch order under synchronous fakes


def test_quorum_returns_m_results():
    flow = quorum(call(mcp("srv", "a")), call(mcp("srv", "b")), call(mcp("srv", "c")), k=2)
    fr, env = _env(flow, tools=TOOLS)
    out = run(interpret(fr.flow, 1, env))
    assert isinstance(out.value, list) and len(out.value) == 2


def test_think_invokes_reasoner():
    flow = think("summarizer")
    fr, env = _env(flow, reasoners={"summarizer": lambda v: f"summary:{v}"})
    assert run(interpret(fr.flow, "doc", env)).value == "summary:doc"


def test_human_gate_uses_gate_handler():
    flow = human_gate()
    fr, env = _env(flow, gate=lambda v: {"approved": True, "echo": v})
    assert run(interpret(fr.flow, 42, env)).value == {"approved": True, "echo": 42}


def test_sub_runs_child_handler():
    flow = sub("child", Contract.pipeline())
    fr, env = _env(flow, subs={"child": lambda v: v * 100})
    assert run(interpret(fr.flow, 3, env)).value == 300


def test_app_runs_agent_handler():
    flow = app("controller")
    fr, env = _env(flow, agents={"controller": lambda v: {"status": "done", "output": v}})
    assert run(interpret(fr.flow, "go", env)).value == {"status": "done", "output": "go"}


def test_stage_compiles_then_runs_plan_with_late_binding():
    # The planner returns an UNFROZEN plan; the interpreter late-binds its calls
    # by tool ref (admission would have vetted them in the real pipeline).
    def planner(value):
        return seq(call(mcp("srv", "inc")), call(mcp("srv", "double")))

    flow = stage("planner")
    fr, env = _env(flow, tools=TOOLS, planners={"planner": planner})
    out = run(interpret(fr.flow, 5, env))
    assert out.value == 12  # plan: (5+1)*2, executed via late-bound tools


def test_max_calls_under_limit_succeeds():
    flow = seq(call(mcp("srv", "inc")), call(mcp("srv", "inc")))
    fr, env = _env(flow, tools=TOOLS, max_calls={"srv/inc": 2})

    out = run(interpret(fr.flow, 5, env))

    assert out.value == 7
    assert env.call_counts == {"srv/inc": 2}


def test_max_calls_over_limit_raises_before_extra_effect():
    calls = {"count": 0}

    def inc(value):
        calls["count"] += 1
        return value + 1

    flow = seq(call(mcp("srv", "inc")), call(mcp("srv", "inc")))
    fr, env = _env(flow, tools={**TOOLS, "srv/inc": inc}, max_calls={"srv/inc": 1})

    with pytest.raises(CapabilityDenied):
        run(interpret(fr.flow, 5, env))

    assert calls["count"] == 1
    assert env.call_counts == {"srv/inc": 1}


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_temporal_env_inherits_call_counts_for_child_flows() -> None:
    async def gate_waiter(value, cid, timeout_s):  # noqa: ANN001
        return value

    env = _TemporalEnv(
        manifest={},
        emitter=ProjectionEmitter(InMemoryProjection()),
        session_id="s",
        manifest_json={},
        policy=ExecutionPolicy(),
        gate_waiter=gate_waiter,
        max_call_limits={"srv/inc": 1},
        call_counts={"srv/inc": 1},
    )

    with pytest.raises(CapabilityDenied):
        env.charge_call("srv/inc")


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_temporal_env_merges_child_agent_call_counts(monkeypatch) -> None:
    from julep.execution import harness
    from julep.execution.harness import ExecutionPolicy, _TemporalEnv
    from julep.projection import InMemoryProjection, ProjectionEmitter

    async def gate_waiter(value, cid, timeout_s):  # noqa: ANN001
        return value

    async def fake_execute_child_workflow(*args, **kwargs):  # noqa: ANN001
        return {
            "status": "done",
            "output": "ok",
            "callCounts": {"srv/inc": 2, "srv/other": "3"},
        }

    monkeypatch.setattr(
        harness.workflow,
        "execute_child_workflow",
        fake_execute_child_workflow,
    )

    env = _TemporalEnv(
        manifest={},
        emitter=ProjectionEmitter(InMemoryProjection()),
        session_id="s",
        manifest_json={},
        policy=ExecutionPolicy(),
        gate_waiter=gate_waiter,
        max_call_limits={"srv/inc": 5, "srv/other": 5},
        call_counts={"srv/inc": 1},
    )

    out = run(env.run_agent("controller", "value", "cid"))
    assert out["output"] == "ok"
    assert env.call_counts_snapshot() == {"srv/inc": 2, "srv/other": 3}


def test_inmemory_env_awaits_async_reasoner():
    """Regression: ``InMemoryEnv.invoke_reasoner`` must await an *async* reasoner.

    The local session backend wraps a real provider call as an async reasoner
    callable. Before the fix, the un-awaited coroutine leaked out of
    ``invoke_reasoner`` and the interpreter raised
    ``Object of type coroutine is not JSON serializable`` (surfaced by the live
    ``examples/session_demo.py local`` run). This mirrors ``run_agent``'s
    existing ``await out if inspect.isawaitable(out)`` handling. Sync reasoners
    must keep working too.
    """

    async def areason(value):
        return {"reply": f"async:{value}"}

    fr, env, _ = _env_and_store(think("r"), reasoners={"r": areason})
    assert run(interpret(fr.flow, "doc", env)).value == {"reply": "async:doc"}

    fr2, env2, _ = _env_and_store(think("r"), reasoners={"r": lambda v: {"reply": f"sync:{v}"}})
    assert run(interpret(fr2.flow, "doc", env2)).value == {"reply": "sync:doc"}
