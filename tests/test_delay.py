"""The reserved __sleep__ leaf: authoring, freeze, and interpretation."""
from __future__ import annotations

import asyncio

import pytest

from composable_agents.derived import delay
from composable_agents.execution.interpreter import InMemoryEnv, interpret
from composable_agents.ir import CallStep, NativeTool, SLEEP_TOOL
from composable_agents.projection import InMemoryProjection, ProjectionEmitter


def _env(**kwargs):
    return InMemoryEnv({}, ProjectionEmitter(InMemoryProjection()), **kwargs)


def test_delay_emits_reserved_call_leaf():
    node = delay(seconds=30)
    assert isinstance(node.step, CallStep)
    assert node.step.tool == NativeTool(SLEEP_TOOL)
    assert node.ann is not None and node.ann.timeout == 30


def test_delay_rejects_nonpositive():
    with pytest.raises(ValueError):
        delay(seconds=0)


def test_interpreter_sleeps_and_passes_value_through():
    env = _env()
    result = asyncio.run(interpret(delay(seconds=7), {"v": 1}, env))
    assert result.value == {"v": 1}
    assert env.sleeps == [7]


def test_inmemory_env_custom_sleeper():
    waited = []

    async def sleeper(seconds):
        waited.append(seconds)

    env = _env(sleeper=sleeper)
    asyncio.run(interpret(delay(seconds=2), "x", env))
    assert waited == [2]


def test_freeze_resolves_sleep_without_snapshot():
    from composable_agents.freeze import McpSnapshot, freeze

    frozen = freeze(delay(seconds=5), McpSnapshot())
    [tool] = list(frozen.manifest.values())
    assert tool.ref == NativeTool(SLEEP_TOOL)
    assert tool.contract.effect.value == "read"
