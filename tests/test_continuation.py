from __future__ import annotations

import asyncio

import pytest

from composable_agents.continuation import (
    CONTINUATION_KEY,
    continuation_value,
    continue_with,
    is_continuation,
    run_chained,
)
from composable_agents.errors import ComposableAgentsError


def test_sentinel_roundtrip():
    s = continue_with({"cursor": 10})
    assert is_continuation(s)
    assert continuation_value(s) == {"cursor": 10}
    assert s[CONTINUATION_KEY] == {"cursor": 10}


def test_plain_values_are_not_continuations():
    for v in (None, 0, "x", [], {"a": 1}, {"__continue___": 1}):
        assert not is_continuation(v)


def test_run_chained_follows_segments():
    async def segment(value):
        n = value["n"]
        return continue_with({"n": n + 1}) if n < 3 else {"done": n}

    out = asyncio.run(run_chained(segment, {"n": 0}))
    assert out == {"done": 3}


def test_run_chained_bounds_segments():
    async def forever(value):
        return continue_with(value)

    with pytest.raises(ComposableAgentsError, match="did not settle"):
        asyncio.run(run_chained(forever, {}, max_segments=5))
