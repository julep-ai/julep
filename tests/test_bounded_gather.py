from __future__ import annotations

import asyncio


def test_gather_bounded_caps_concurrency():
    from julep.execution.interpreter import gather_bounded

    state = {"now": 0, "peak": 0}

    async def job(i):
        state["now"] += 1
        state["peak"] = max(state["peak"], state["now"])
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        state["now"] -= 1
        return i

    out = asyncio.run(gather_bounded([job(i) for i in range(8)], max_parallel=2))
    assert out == list(range(8))
    assert state["peak"] <= 2


def test_gather_bounded_none_is_unbounded():
    from julep.execution.interpreter import gather_bounded

    async def job(i):
        return i * 2

    out = asyncio.run(gather_bounded([job(i) for i in range(4)], max_parallel=None))
    assert out == [0, 2, 4, 6]


def test_policy_roundtrips_max_parallel():
    from julep.execution.policy import ExecutionPolicy

    p = ExecutionPolicy(max_parallel=4)
    assert ExecutionPolicy.from_json(p.to_json()).max_parallel == 4
    assert ExecutionPolicy.from_json({}).max_parallel is None


def test_inmemory_env_accepts_max_parallel():
    from julep.execution.interpreter import InMemoryEnv
    from julep.projection import InMemoryProjection, ProjectionEmitter

    env = InMemoryEnv({}, ProjectionEmitter(InMemoryProjection()), max_parallel=3)
    assert env.max_parallel == 3
