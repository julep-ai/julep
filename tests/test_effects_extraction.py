"""The effects layer must be importable and usable without temporalio."""
from __future__ import annotations

import asyncio

import pytest
import subprocess
import sys
from typing import Any

from julep import HAVE_TEMPORAL


def test_effects_importable_without_temporalio():
    code = (
        "import builtins\n"
        "real_import = builtins.__import__\n"
        "def block(name, *a, **k):\n"
        "    if name.split('.')[0] == 'temporalio':\n"
        "        raise ImportError('temporalio blocked by test')\n"
        "    return real_import(name, *a, **k)\n"
        "builtins.__import__ = block\n"
        "import julep.execution.effects\n"
        "import julep.execution.policy\n"
        "print('ok')\n"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "ok" in out.stdout


def test_run_call_effect_routes_mcp():
    from julep.execution.effects import (
        CallToolInput, WorkerContext, callTool, configure,
    )

    seen = {}

    async def fake_mcp(server, tool, value, key):
        seen.update(server=server, tool=tool, value=value, key=key)
        return {"hits": 3}

    configure(WorkerContext(mcp_call=fake_mcp))
    inp = CallToolInput(
        tool_ref={"kind": "mcp", "server": "kb", "tool": "search"},
        value={"q": "x"}, cid="cid-1",
    )
    result = asyncio.run(callTool(inp))
    assert result == {"hits": 3}
    assert seen == {"server": "kb", "tool": "search", "value": {"q": "x"}, "key": "cid-1"}


def test_mcp_call_validates_frozen_input_schema_before_network():
    from julep.errors import ToolInputValidation
    from julep.execution.effects import (
        CallToolInput, WorkerContext, callTool, configure,
    )

    calls: list[Any] = []

    async def fake_mcp(server, tool, value, key, principal, secrets, validated):
        calls.append((server, tool, value, key, principal, secrets, validated))
        return {"ok": True}

    configure(WorkerContext(mcp_call=fake_mcp))
    inp = CallToolInput(
        tool_ref={"kind": "mcp", "server": "kb", "tool": "search"},
        value={"q": 7},
        cid="cid-invalid",
        frozen_input_schema={
            "type": "object",
            "properties": {"q": {"type": "string"}},
            "required": ["q"],
        },
    )

    with pytest.raises(ToolInputValidation):
        asyncio.run(callTool(inp))
    assert calls == []


@pytest.mark.parametrize(
    ("frozen_schema", "workflow_validated", "expected"),
    [
        ({"type": "object"}, False, True),
        (None, True, True),
        (None, False, False),
    ],
)
def test_mcp_call_carries_trusted_schema_validation(
    frozen_schema: dict[str, Any] | None,
    workflow_validated: bool,
    expected: bool,
):
    from julep.execution.effects import (
        CallToolInput, WorkerContext, callTool, configure,
    )

    seen: list[bool] = []

    async def fake_mcp(server, tool, value, key, principal, secrets, validated):
        seen.append(validated)
        return {"ok": True}

    configure(WorkerContext(mcp_call=fake_mcp))
    inp = CallToolInput(
        tool_ref={"kind": "mcp", "server": "kb", "tool": "search"},
        value={"q": "x"},
        cid="cid-valid",
        frozen_input_schema=frozen_schema,
        input_schema_validated=workflow_validated,
    )

    assert asyncio.run(callTool(inp)) == {"ok": True}
    assert seen == [expected]


def test_toolref_json_roundtrip():
    from julep.execution.effects import toolref_json_from_key

    assert toolref_json_from_key("kb/search") == {"kind": "mcp", "server": "kb", "tool": "search"}
    assert toolref_json_from_key("fetch") == {"kind": "native", "name": "fetch"}


def test_worker_context_defaults_to_default_resolve_qos():
    from julep.execution.effects import WorkerContext
    from julep.qos import default_resolve_qos

    assert WorkerContext().resolve_qos is default_resolve_qos


def _configure_restoring(ctx):
    """configure(ctx) but restore the previous global _CTX afterward.

    The resolveQoS tests install a custom registry; without restoring the
    process-global _CTX they would leak that registry into later tests that
    rely on DEFAULT_REGISTRY (e.g. test_prompt_renderers).
    """
    from julep.execution import effects as _effects
    from julep.execution.effects import configure

    prev = _effects._CTX
    configure(ctx)
    return prev


def _restore_ctx(prev):
    from julep.execution import effects as _effects

    _effects._CTX = prev


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_resolve_qos_activity_clamps_non_batchable_batch_request():
    from julep.dotctx import Reasoner
    from julep.execution.effects import (
        ResolveQoSInput, WorkerContext, resolveQoS,
    )
    from julep.registry import Registry

    registry = Registry()
    registry.register_reasoner(Reasoner(name="b", model="test", system="s"))
    prev = _configure_restoring(WorkerContext(registry=registry))
    try:
        inp = ResolveQoSInput(
            reasoner="b",
            node_batchable=False,
            principal={"qos": "BATCH"},
        )
        assert asyncio.run(resolveQoS(inp)) == "FLEX"
    finally:
        _restore_ctx(prev)


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_resolve_qos_activity_allows_batch_for_batchable_node():
    from julep.dotctx import Reasoner
    from julep.execution.effects import (
        ResolveQoSInput, WorkerContext, resolveQoS,
    )
    from julep.registry import Registry

    registry = Registry()
    registry.register_reasoner(Reasoner(name="b", model="test", system="s"))
    prev = _configure_restoring(WorkerContext(registry=registry))
    try:
        inp = ResolveQoSInput(
            reasoner="b",
            node_batchable=True,
            principal={"qos": "BATCH"},
        )
        assert asyncio.run(resolveQoS(inp)) == "BATCH"
    finally:
        _restore_ctx(prev)


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_resolve_qos_activity_honors_worker_context_resolver_override():
    from julep.dotctx import Reasoner
    from julep.execution.effects import (
        ResolveQoSInput, WorkerContext, resolveQoS,
    )
    from julep.qos import QoSTier
    from julep.registry import Registry

    registry = Registry()
    registry.register_reasoner(Reasoner(name="b", model="test", system="s"))

    def resolve_priority(*args, **kwargs):
        return QoSTier.PRIORITY

    prev = _configure_restoring(
        WorkerContext(registry=registry, resolve_qos=resolve_priority)
    )
    try:
        inp = ResolveQoSInput(
            reasoner="b",
            node_batchable=True,
            principal={"qos": "BATCH"},
        )
        assert asyncio.run(resolveQoS(inp)) == "PRIORITY"
    finally:
        _restore_ctx(prev)


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_activities_reexport_worker_context():
    # Backward compat: existing imports from .activities keep working.
    from julep.execution.activities import WorkerContext as A
    from julep.execution.effects import WorkerContext as E

    assert A is E


def test_reasoner_dispatch_defaults():
    import dataclasses

    from julep.qos import ReasonerDispatch, QoSTier

    d = ReasonerDispatch()
    assert d.qos is QoSTier.STANDARD
    assert d.batch_id is None
    assert dataclasses.is_dataclass(ReasonerDispatch)
    assert ReasonerDispatch.__dataclass_params__.frozen is True


def test_adapt_llm_caller_legacy_2_3_4_arg_get_default_dispatch():
    from conftest import run

    from julep.dotctx import Reasoner
    from julep.execution.effects import _adapt_llm_caller
    from julep.qos import ReasonerDispatch, QoSTier

    sentinel_2 = object()
    sentinel_3 = object()
    sentinel_4 = object()
    reasoner = Reasoner(name="t", model="m", system="s")
    value = {"v": 1}
    principal = {"tenant": "t"}

    async def fake_2(reasoner, value):
        return sentinel_2

    async def fake_3(reasoner, value, principal):
        return sentinel_3

    async def fake_4(reasoner, value, principal, transcript):
        return sentinel_4

    for fn, sentinel in (
        (fake_2, sentinel_2),
        (fake_3, sentinel_3),
        (fake_4, sentinel_4),
    ):
        adapted = _adapt_llm_caller(fn)
        result = run(
            adapted(
                reasoner,
                value,
                principal,
                None,
                ReasonerDispatch(qos=QoSTier.FLEX),
            )
        )
        assert result is sentinel


def test_adapt_llm_caller_5arg_receives_dispatch():
    from conftest import run

    from julep.dotctx import Reasoner
    from julep.execution.effects import _adapt_llm_caller
    from julep.qos import ReasonerDispatch, QoSTier

    async def fake_5(reasoner, value, principal, transcript, dispatch):
        return dispatch.qos

    adapted = _adapt_llm_caller(fake_5)
    result = run(
        adapted(
            Reasoner(name="t", model="m", system="s"),
            {"v": 1},
            {"tenant": "t"},
            None,
            ReasonerDispatch(qos=QoSTier.PRIORITY),
        )
    )
    assert result is QoSTier.PRIORITY


def test_invoke_reasoner_passes_dispatch_qos_to_llm():
    from conftest import run

    from julep.dotctx import Reasoner
    from julep.execution import effects
    from julep.execution.effects import InvokeReasonerInput, WorkerContext
    from julep.qos import ReasonerDispatch, QoSTier
    from julep.registry import Registry

    registry = Registry()
    registry.register_reasoner(Reasoner(name="b", model="test", system="s"))
    captured: dict[str, ReasonerDispatch] = {}

    async def fake_llm(reasoner, value, principal, transcript, dispatch):
        captured["dispatch"] = dispatch
        return "ok"

    prev = _configure_restoring(WorkerContext(llm=fake_llm, registry=registry))
    try:
        result = run(
            effects.invokeReasoner(
                InvokeReasonerInput(reasoner="b", value="hi", cid="think@1", qos="FLEX")
            )
        )
    finally:
        _restore_ctx(prev)

    assert result == "ok"
    assert captured["dispatch"].qos is QoSTier.FLEX


def test_invoke_reasoner_clamps_batch_qos_to_standard():
    from conftest import run

    from julep.dotctx import Reasoner
    from julep.execution import effects
    from julep.execution.effects import InvokeReasonerInput, WorkerContext
    from julep.qos import ReasonerDispatch, QoSTier
    from julep.registry import Registry

    registry = Registry()
    registry.register_reasoner(Reasoner(name="b", model="test", system="s"))
    captured: dict[str, ReasonerDispatch] = {}

    async def fake_llm(reasoner, value, principal, transcript, dispatch):
        captured["dispatch"] = dispatch
        return "ok"

    prev = _configure_restoring(WorkerContext(llm=fake_llm, registry=registry))
    try:
        result = run(
            effects.invokeReasoner(
                InvokeReasonerInput(reasoner="b", value="hi", cid="think@1", qos="BATCH")
            )
        )
    finally:
        _restore_ctx(prev)

    assert result == "ok"
    assert captured["dispatch"].qos is QoSTier.STANDARD


def test_invoke_reasoner_default_qos_is_standard():
    from conftest import run

    from julep.dotctx import Reasoner
    from julep.execution import effects
    from julep.execution.effects import InvokeReasonerInput, WorkerContext
    from julep.qos import ReasonerDispatch, QoSTier
    from julep.registry import Registry

    registry = Registry()
    registry.register_reasoner(Reasoner(name="b", model="test", system="s"))
    captured: dict[str, ReasonerDispatch] = {}

    async def fake_llm(reasoner, value, principal, transcript, dispatch):
        captured["dispatch"] = dispatch
        return "ok"

    prev = _configure_restoring(WorkerContext(llm=fake_llm, registry=registry))
    try:
        result = run(
            effects.invokeReasoner(
                InvokeReasonerInput(reasoner="b", value="hi", cid="think@1")
            )
        )
    finally:
        _restore_ctx(prev)

    assert result == "ok"
    assert captured["dispatch"].qos is QoSTier.STANDARD


def test_resolve_agent_spec_builds_tool_defs_from_registered_expectations():
    from conftest import run

    from julep.execution import effects
    from julep.execution.effects import WorkerContext
    from julep.registry import Registry, ToolSchemaExpectation

    schema = {"type": "object", "properties": {"q": {"type": "string"}}}
    registry = Registry()
    registry.register_tool_expectation(
        ToolSchemaExpectation(key="search", input_schema=schema, ctx_path="tools.pyi")
    )
    prev = _configure_restoring(
        WorkerContext(
            registry=registry,
            agents={
                "ctrl": {
                    "config": {"nativeTools": True},
                    "grantedTools": ["search"],
                }
            },
        )
    )
    try:
        spec = run(effects.resolveAgentSpec("ctrl"))
    finally:
        _restore_ctx(prev)

    assert spec["toolDefs"] == [
        {
            "type": "function",
            "function": {
                "name": "search",
                "description": "",
                "parameters": schema,
            },
        }
    ]


def test_resolve_agent_spec_passes_through_spec_level_tool_defs():
    from conftest import run

    from julep.execution import effects
    from julep.execution.effects import WorkerContext
    from julep.registry import Registry

    tool_defs = [
        {
            "type": "function",
            "function": {
                "name": "lookup",
                "description": "Lookup",
                "parameters": {"type": "object"},
            },
        }
    ]
    prev = _configure_restoring(
        WorkerContext(
            registry=Registry(),
            agents={
                "ctrl": {
                    "config": {"nativeTools": True},
                    "grantedTools": ["lookup"],
                    "toolDefs": tool_defs,
                }
            },
        )
    )
    try:
        spec = run(effects.resolveAgentSpec("ctrl"))
    finally:
        _restore_ctx(prev)

    assert spec["toolDefs"] is tool_defs


def test_resolve_agent_spec_native_tools_without_expectation_errors():
    from conftest import run

    from julep.execution import effects
    from julep.execution.effects import WorkerContext
    from julep.registry import Registry

    prev = _configure_restoring(
        WorkerContext(
            registry=Registry(),
            agents={
                "ctrl": {
                    "config": {"nativeTools": True},
                    "grantedTools": ["missing"],
                }
            },
        )
    )
    try:
        with pytest.raises(RuntimeError, match="Tool 'missing'.*ToolSchemaExpectation"):
            run(effects.resolveAgentSpec("ctrl"))
    finally:
        _restore_ctx(prev)


def test_invoke_reasoner_forwards_tools_keyword_only_when_present():
    from conftest import run

    from julep.dotctx import Reasoner
    from julep.execution import effects
    from julep.execution.effects import InvokeReasonerInput, WorkerContext
    from julep.registry import Registry

    registry = Registry()
    registry.register_reasoner(Reasoner(name="b", model="test", system="s"))
    captured: dict[str, Any] = {}
    tool_defs = [{"type": "function", "function": {"name": "lookup"}}]

    async def fake_llm(reasoner, value, principal, transcript, dispatch, *, tools=None):
        captured["tools"] = tools
        return "ok"

    prev = _configure_restoring(WorkerContext(llm=fake_llm, registry=registry))
    try:
        result = run(
            effects.invokeReasoner(
                InvokeReasonerInput(
                    reasoner="b",
                    value="hi",
                    cid="think@1",
                    tools=tool_defs,
                )
            )
        )
    finally:
        _restore_ctx(prev)

    assert result == "ok"
    assert captured["tools"] == tool_defs

    async def no_kwargs_llm(reasoner, value, principal, transcript, dispatch):
        return "legacy-ok"

    prev = _configure_restoring(WorkerContext(llm=no_kwargs_llm, registry=registry))
    try:
        result = run(
            effects.invokeReasoner(
                InvokeReasonerInput(reasoner="b", value="hi", cid="think@2")
            )
        )
    finally:
        _restore_ctx(prev)

    assert result == "legacy-ok"
