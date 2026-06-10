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


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_activities_reexport_worker_context():
    # Backward compat: existing imports from .activities keep working.
    from composable_agents.execution.activities import WorkerContext as A
    from composable_agents.execution.effects import WorkerContext as E

    assert A is E
