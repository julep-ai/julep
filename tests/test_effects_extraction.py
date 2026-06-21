"""The effects layer must be importable and usable without temporalio."""
from __future__ import annotations

import asyncio

import pytest
import subprocess
import sys

from composable_agents import HAVE_TEMPORAL


def test_effects_importable_without_temporalio():
    code = (
        "import builtins\n"
        "real_import = builtins.__import__\n"
        "def block(name, *a, **k):\n"
        "    if name.split('.')[0] == 'temporalio':\n"
        "        raise ImportError('temporalio blocked by test')\n"
        "    return real_import(name, *a, **k)\n"
        "builtins.__import__ = block\n"
        "import composable_agents.execution.effects\n"
        "import composable_agents.execution.policy\n"
        "print('ok')\n"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "ok" in out.stdout


def test_call_hand_effect_routes_mcp():
    from composable_agents.execution.effects import (
        CallHandInput, WorkerContext, callHand, configure,
    )

    seen = {}

    async def fake_mcp(server, tool, value, key):
        seen.update(server=server, tool=tool, value=value, key=key)
        return {"hits": 3}

    configure(WorkerContext(mcp_call=fake_mcp))
    inp = CallHandInput(
        tool_ref={"kind": "mcp", "server": "kb", "tool": "search"},
        value={"q": "x"}, cid="cid-1",
    )
    result = asyncio.run(callHand(inp))
    assert result == {"hits": 3}
    assert seen == {"server": "kb", "tool": "search", "value": {"q": "x"}, "key": "cid-1"}


def test_toolref_json_roundtrip():
    from composable_agents.execution.effects import toolref_json_from_key

    assert toolref_json_from_key("kb/search") == {"kind": "mcp", "server": "kb", "tool": "search"}
    assert toolref_json_from_key("fetch") == {"kind": "native", "name": "fetch"}


def test_worker_context_defaults_to_default_resolve_qos():
    from composable_agents.execution.effects import WorkerContext
    from composable_agents.qos import default_resolve_qos

    assert WorkerContext().resolve_qos is default_resolve_qos


def _configure_restoring(ctx):
    """configure(ctx) but restore the previous global _CTX afterward.

    The resolveQoS tests install a custom registry; without restoring the
    process-global _CTX they would leak that registry into later tests that
    rely on DEFAULT_REGISTRY (e.g. test_prompt_renderers).
    """
    from composable_agents.execution import effects as _effects
    from composable_agents.execution.effects import configure

    prev = _effects._CTX
    configure(ctx)
    return prev


def _restore_ctx(prev):
    from composable_agents.execution import effects as _effects

    _effects._CTX = prev


def test_resolve_qos_activity_clamps_non_batchable_batch_request():
    from composable_agents.dotctx import Brain
    from composable_agents.execution.effects import (
        ResolveQoSInput, WorkerContext, resolveQoS,
    )
    from composable_agents.registry import Registry

    registry = Registry()
    registry.register_brain(Brain(name="b", model="test", system="s"))
    prev = _configure_restoring(WorkerContext(registry=registry))
    try:
        inp = ResolveQoSInput(
            brain="b",
            node_batchable=False,
            principal={"qos": "BATCH"},
        )
        assert asyncio.run(resolveQoS(inp)) == "FLEX"
    finally:
        _restore_ctx(prev)


def test_resolve_qos_activity_allows_batch_for_batchable_node():
    from composable_agents.dotctx import Brain
    from composable_agents.execution.effects import (
        ResolveQoSInput, WorkerContext, resolveQoS,
    )
    from composable_agents.registry import Registry

    registry = Registry()
    registry.register_brain(Brain(name="b", model="test", system="s"))
    prev = _configure_restoring(WorkerContext(registry=registry))
    try:
        inp = ResolveQoSInput(
            brain="b",
            node_batchable=True,
            principal={"qos": "BATCH"},
        )
        assert asyncio.run(resolveQoS(inp)) == "BATCH"
    finally:
        _restore_ctx(prev)


def test_resolve_qos_activity_honors_worker_context_resolver_override():
    from composable_agents.dotctx import Brain
    from composable_agents.execution.effects import (
        ResolveQoSInput, WorkerContext, resolveQoS,
    )
    from composable_agents.qos import QoSTier
    from composable_agents.registry import Registry

    registry = Registry()
    registry.register_brain(Brain(name="b", model="test", system="s"))

    def resolve_priority(*args, **kwargs):
        return QoSTier.PRIORITY

    prev = _configure_restoring(
        WorkerContext(registry=registry, resolve_qos=resolve_priority)
    )
    try:
        inp = ResolveQoSInput(
            brain="b",
            node_batchable=True,
            principal={"qos": "BATCH"},
        )
        assert asyncio.run(resolveQoS(inp)) == "PRIORITY"
    finally:
        _restore_ctx(prev)


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_activities_reexport_worker_context():
    # Backward compat: existing imports from .activities keep working.
    from composable_agents.execution.activities import WorkerContext as A
    from composable_agents.execution.effects import WorkerContext as E

    assert A is E
