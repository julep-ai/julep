"""Invariant 4: race-family concurrency settles on success."""

from __future__ import annotations

import asyncio

import pytest

from composable_agents import call, freeze, hedge, mcp, quorum, race
from composable_agents.errors import RaceAllFailed
from composable_agents.execution.interpreter import interpret, race_first_from_thunks
from composable_agents.projection import InMemoryProjection, ProjectionEmitter
from conftest import read_snapshot, run
from tests.invariants.helpers import AsyncInMemoryEnv, fast_fail, slow_ok


def _env(flow, **kw):
    fr = freeze(flow, read_snapshot("a", "b", "c"))
    store = InMemoryProjection()
    return fr, AsyncInMemoryEnv(fr.manifest, ProjectionEmitter(store), **kw)


def test_race_ignores_fast_failure_and_returns_slow_success():
    flow = race(call(mcp("srv", "a")), call(mcp("srv", "b")))
    fr, env = _env(flow, hands={
        "srv/a": fast_fail(RuntimeError("fast boom")),
        "srv/b": slow_ok(0.01, "slow-ok"),
    })

    out = run(interpret(fr.flow, "input", env))

    assert out.value == "slow-ok"


def test_race_all_failures_raise_aggregate():
    flow = race(call(mcp("srv", "a")), call(mcp("srv", "b")))
    fr, env = _env(flow, hands={
        "srv/a": fast_fail(RuntimeError("boom-a")),
        "srv/b": fast_fail(ValueError("boom-b")),
    })

    with pytest.raises(RaceAllFailed) as excinfo:
        run(interpret(fr.flow, "input", env))

    assert [type(e) for e in excinfo.value.failures] == [RuntimeError, ValueError]
    assert [str(e) for e in excinfo.value.failures] == ["boom-a", "boom-b"]


def test_race_cancels_losing_branches_after_success():
    sink: list[str] = []

    async def records_after_delay(_value):
        await asyncio.sleep(0.05)
        sink.append("loser-ran")
        return "loser"

    async def scenario():
        flow = race(call(mcp("srv", "a")), call(mcp("srv", "b")))
        fr, env = _env(flow, hands={
            "srv/a": slow_ok(0.01, "winner"),
            "srv/b": records_after_delay,
        })

        out = await interpret(fr.flow, "input", env)
        await asyncio.sleep(0.06)
        return out

    out = run(scenario())

    assert out.value == "winner"
    assert sink == []


def test_quorum_returns_successes_in_branch_order_and_ignores_failure():
    flow = quorum(
        call(mcp("srv", "a")),
        call(mcp("srv", "b")),
        call(mcp("srv", "c")),
        k=2,
    )
    fr, env = _env(flow, hands={
        "srv/a": slow_ok(0.02, "a-ok"),
        "srv/b": fast_fail(RuntimeError("boom-b")),
        "srv/c": slow_ok(0.01, "c-ok"),
    })

    out = run(interpret(fr.flow, "input", env))

    assert out.value == ["a-ok", "c-ok"]


def test_quorum_raises_when_k_successes_are_unreachable():
    flow = quorum(
        call(mcp("srv", "a")),
        call(mcp("srv", "b")),
        call(mcp("srv", "c")),
        k=2,
    )
    fr, env = _env(flow, hands={
        "srv/a": fast_fail(RuntimeError("boom-a")),
        "srv/b": fast_fail(ValueError("boom-b")),
        "srv/c": slow_ok(0.05, "too-late"),
    })

    with pytest.raises(RaceAllFailed) as excinfo:
        run(interpret(fr.flow, "input", env))

    assert [type(e) for e in excinfo.value.failures] == [RuntimeError, ValueError]


def test_hedge_does_not_invoke_later_thunks_when_primary_wins_before_delay():
    invocations = {"b": 0}

    async def branch_b(_value):
        invocations["b"] += 1
        return "b-ok"

    flow = hedge(call(mcp("srv", "a")), call(mcp("srv", "b")), hedge_ms=50)
    fr, env = _env(flow, hands={
        "srv/a": slow_ok(0.01, "a-ok"),
        "srv/b": branch_b,
    })

    out = run(interpret(fr.flow, "input", env))

    assert out.value == "a-ok"
    assert invocations == {"b": 0}


@pytest.mark.parametrize("hedge_ms", [0, None])
def test_hedge_without_positive_delay_invokes_all_thunks_before_waiting(hedge_ms):
    invocations: list[str] = []
    observed_at_first_start: list[tuple[str, ...]] = []

    def thunk(name: str):
        def start():
            invocations.append(name)

            async def branch():
                if name == "a":
                    observed_at_first_start.append(tuple(invocations))
                return name

            return branch()

        return start

    async def wait_first(waitset):
        done, pending = await asyncio.wait(waitset, return_when=asyncio.FIRST_COMPLETED)
        return set(done), set(pending)

    winner = run(
        race_first_from_thunks(
            [thunk("a"), thunk("b"), thunk("c")],
            kind="hedge",
            m=1,
            hedge_ms=hedge_ms,
            wait_first=wait_first,
        )
    )

    assert winner == "a"
    assert invocations == ["a", "b", "c"]
    assert observed_at_first_start == [("a", "b", "c")]


def test_hedge_starts_next_branch_after_delay_and_fallback_can_win():
    invocations = {"b": 0}

    async def branch_b(_value):
        invocations["b"] += 1
        await asyncio.sleep(0.001)
        return "b-ok"

    flow = hedge(call(mcp("srv", "a")), call(mcp("srv", "b")), hedge_ms=10)
    fr, env = _env(flow, hands={
        "srv/a": slow_ok(0.05, "a-ok"),
        "srv/b": branch_b,
    })

    out = run(interpret(fr.flow, "input", env))

    assert out.value == "b-ok"
    assert invocations == {"b": 1}


def test_race_over_instant_successes_picks_branch_zero():
    flow = race(call(mcp("srv", "a")), call(mcp("srv", "b")))
    fr, env = _env(flow, hands={
        "srv/a": lambda _value: "a-ok",
        "srv/b": lambda _value: "b-ok",
    })

    out = run(interpret(fr.flow, "input", env))

    assert out.value == "a-ok"
