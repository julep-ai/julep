"""Pure interpreter control-flow tests (InMemoryEnv, no Temporal)."""

from __future__ import annotations

from composable_agents import (
    call, mcp, think, seq, par, alt, iter_up_to, stage, app,
    sub, race, quorum, human_gate, Contract, freeze, register_pure,
)
from composable_agents.execution.interpreter import InMemoryEnv, interpret
from composable_agents.projection import InMemoryProjection, ProjectionEmitter
from conftest import read_snapshot, run


def _env(flow, **kw):
    fr = freeze(flow, read_snapshot("inc", "double", "half", "a", "b", "c"))
    store = InMemoryProjection()
    return fr, InMemoryEnv(fr.manifest, ProjectionEmitter(store), **kw)


HANDS = {
    "srv/inc": lambda v: v + 1,
    "srv/double": lambda v: v * 2,
    "srv/half": lambda v: v // 2,
    "srv/a": lambda v: ("a", v),
    "srv/b": lambda v: ("b", v),
    "srv/c": lambda v: ("c", v),
}


def test_pipeline_threads_value():
    flow = seq(call(mcp("srv", "inc")), call(mcp("srv", "double")))
    fr, env = _env(flow, hands=HANDS)
    out = run(interpret(fr.flow, 5, env))
    assert out.value == 12  # (5+1)*2


def test_parallel_collects_branches():
    flow = par(call(mcp("srv", "a")), call(mcp("srv", "b")))
    fr, env = _env(flow, hands=HANDS)
    out = run(interpret(fr.flow, 9, env))
    assert out.value == [("a", 9), ("b", 9)]


def test_alt_routes_by_pure_predicate():
    register_pure("is_even", lambda v: v % 2 == 0)
    flow = alt("is_even", call(mcp("srv", "half")), call(mcp("srv", "inc")))
    fr, env = _env(flow, hands=HANDS)
    assert run(interpret(fr.flow, 8, env)).value == 4   # even -> half
    fr2, env2 = _env(flow, hands=HANDS)
    assert run(interpret(fr2.flow, 7, env2)).value == 8  # odd -> inc


def test_iter_up_to_runs_bound_times_and_converges():
    register_pure("at_least_10", lambda v: v >= 10)
    # No convergence: runs exactly bound times.
    flow = iter_up_to(3, call(mcp("srv", "inc")))
    fr, env = _env(flow, hands=HANDS)
    assert run(interpret(fr.flow, 5, env)).value == 8  # 5 -> 6 -> 7 -> 8
    # With convergence: stops early once predicate holds.
    flow2 = iter_up_to(100, call(mcp("srv", "inc")), until="at_least_10")
    fr2, env2 = _env(flow2, hands=HANDS)
    assert run(interpret(fr2.flow, 7, env2)).value == 10  # stops at 10


def test_race_picks_first_branch_with_sync_fakes():
    flow = race(call(mcp("srv", "a")), call(mcp("srv", "b")))
    fr, env = _env(flow, hands=HANDS)
    out = run(interpret(fr.flow, 1, env))
    assert out.value == ("a", 1)  # branch order under synchronous fakes


def test_quorum_returns_m_results():
    flow = quorum(call(mcp("srv", "a")), call(mcp("srv", "b")), call(mcp("srv", "c")), k=2)
    fr, env = _env(flow, hands=HANDS)
    out = run(interpret(fr.flow, 1, env))
    assert isinstance(out.value, list) and len(out.value) == 2


def test_think_invokes_brain():
    flow = think("summarizer")
    fr, env = _env(flow, brains={"summarizer": lambda v: f"summary:{v}"})
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
    fr, env = _env(flow, hands=HANDS, planners={"planner": planner})
    out = run(interpret(fr.flow, 5, env))
    assert out.value == 12  # plan: (5+1)*2, executed via late-bound hands
