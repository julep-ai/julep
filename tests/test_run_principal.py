"""Run-scoped principal threading (docs/design/run-principal.md).

The principal is opaque workflow input: dispatch supplies it, the env stamps it
into every effect payload, callers receive it as one trailing argument, children
and continue-as-new segments inherit it unchanged, and the frozen artifact never
sees it (the golden corpus pins that separately).
"""
from __future__ import annotations

import asyncio
import inspect
from typing import Any

import pytest

from julep import call, ident, mcp, native, register_pure
from julep.continuation import continue_with
from julep.dotctx import Reasoner
from julep.registry import DEFAULT_REGISTRY
from julep.errors import PrincipalRequired
from julep.execution import HAVE_DBOS, HAVE_TEMPORAL
from julep.execution.effects import (
    CallToolInput,
    CompilePlanInput,
    InvokeReasonerInput,
    ResolveQoSInput,
    VerifyPuresInput,
    WorkerContext,
    callTool,
    compilePlan,
    configure,
    invokeReasoner,
    resolveSubflow,
)
from julep.execution.interpreter import InMemoryEnv, interpret
from julep.projection import InMemoryProjection, ProjectionEmitter

PRINCIPAL = {"storeId": 413, "tokenRef": "cred_abc"}
BUNDLE_REF = [{"bundleHash": "a" * 64, "signatureDigest": "b" * 64}]


def _emitter() -> ProjectionEmitter:
    return ProjectionEmitter(InMemoryProjection())


# --------------------------------------------------------------------------- #
# Arity shim: configure() wraps legacy callers once; new callers get the
# principal positionally.
# --------------------------------------------------------------------------- #
def test_legacy_mcp_caller_still_works():
    seen = {}

    async def legacy(server, tool, value, key):
        seen.update(server=server, tool=tool, value=value, key=key)
        return {"hits": 1}

    configure(WorkerContext(mcp_call=legacy))
    inp = CallToolInput(
        tool_ref={"kind": "mcp", "server": "kb", "tool": "search"},
        value={"q": "x"}, cid="cid-1", principal=PRINCIPAL,
    )
    assert asyncio.run(callTool(inp)) == {"hits": 1}
    assert seen == {"server": "kb", "tool": "search", "value": {"q": "x"}, "key": "cid-1"}


def test_new_mcp_caller_receives_principal():
    seen = {}

    async def new_style(server, tool, value, key, principal):
        seen.update(key=key, principal=principal)
        return {"hits": 2}

    configure(WorkerContext(mcp_call=new_style))
    inp = CallToolInput(
        tool_ref={"kind": "mcp", "server": "kb", "tool": "search"},
        value={"q": "x"}, cid="cid-2", principal=PRINCIPAL,
    )
    assert asyncio.run(callTool(inp)) == {"hits": 2}
    assert seen == {"key": "cid-2", "principal": PRINCIPAL}

    # No principal supplied -> the caller sees None, not a stale value.
    asyncio.run(callTool(CallToolInput(
        tool_ref={"kind": "mcp", "server": "kb", "tool": "search"},
        value={}, cid="cid-3",
    )))
    assert seen["principal"] is None


def test_legacy_and_new_llm_callers():
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="principal-reasoner", model="test", system="s"))
    seen: dict[str, Any] = {}

    async def legacy(reasoner, value):
        seen["legacy"] = value
        return {"out": 1}

    configure(WorkerContext(llm=legacy))
    out = asyncio.run(invokeReasoner(InvokeReasonerInput(
        reasoner="principal-reasoner", value=5, cid="c1", principal=PRINCIPAL,
    )))
    assert out == {"out": 1} and seen["legacy"] == 5

    async def new_style(reasoner, value, principal):
        seen["principal"] = principal
        return {"out": 2}

    configure(WorkerContext(llm=new_style))
    out = asyncio.run(invokeReasoner(InvokeReasonerInput(
        reasoner="principal-reasoner", value=5, cid="c2", principal=PRINCIPAL,
    )))
    assert out == {"out": 2} and seen["principal"] == PRINCIPAL


def test_compile_plan_passes_principal_to_llm():
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="principal-planner", model="test", system="plan"))
    seen = {}

    async def planner_llm(reasoner, value, principal):
        seen["principal"] = principal
        return ident().to_json()

    configure(WorkerContext(llm=planner_llm))
    plan = asyncio.run(compilePlan(CompilePlanInput(
        planner="principal-planner", value={}, cid="c1", principal=PRINCIPAL,
    )))
    assert plan["op"] == "ident"
    assert seen["principal"] == PRINCIPAL


def test_configure_twice_does_not_double_wrap():
    calls = []

    async def legacy(server, tool, value, key):
        calls.append((server, tool, value, key))
        return "ok"

    ctx = WorkerContext(mcp_call=legacy)
    configure(ctx)
    configure(ctx)  # second configure must not re-wrap the already-adapted caller
    inp = CallToolInput(
        tool_ref={"kind": "mcp", "server": "kb", "tool": "t"},
        value=1, cid="c", principal=PRINCIPAL,
    )
    assert asyncio.run(callTool(inp)) == "ok"
    assert calls == [("kb", "t", 1, "c")]


def test_caller_can_require_principal():
    async def strict(server, tool, value, key, principal):
        if principal is None:
            raise PrincipalRequired("this worker is multi-tenant; dispatch a principal")
        return "ok"

    configure(WorkerContext(mcp_call=strict))
    ref = {"kind": "mcp", "server": "kb", "tool": "t"}
    assert asyncio.run(callTool(CallToolInput(tool_ref=ref, value=1, cid="c", principal=PRINCIPAL))) == "ok"
    with pytest.raises(PrincipalRequired):
        asyncio.run(callTool(CallToolInput(tool_ref=ref, value=1, cid="c")))


# --------------------------------------------------------------------------- #
# Native tools: principal resolves to transport headers via principal_headers.
# --------------------------------------------------------------------------- #
class _FakeResponse:
    def raise_for_status(self) -> None:
        pass

    def json(self) -> Any:
        return {"ok": True}


class _FakeAsyncClient:
    posted: list[dict[str, Any]] = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, json=None, headers=None):
        _FakeAsyncClient.posted.append({"url": url, "json": json, "headers": headers})
        return _FakeResponse()


def _native_tool_post(monkeypatch, ctx: WorkerContext, inp: CallToolInput) -> dict[str, Any]:
    httpx = pytest.importorskip("httpx")

    _FakeAsyncClient.posted = []
    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)
    configure(ctx)
    assert asyncio.run(callTool(inp)) == {"ok": True}
    (posted,) = _FakeAsyncClient.posted
    return posted


def test_native_tool_principal_headers(monkeypatch):
    posted = _native_tool_post(
        monkeypatch,
        WorkerContext(
            tool_urls={"h": "http://tools.local/h"},
            principal_headers=lambda p: {"X-Store-Id": str(p["storeId"])},
        ),
        CallToolInput(
            tool_ref={"kind": "native", "name": "h"}, value=1, cid="c1",
            principal=PRINCIPAL,
        ),
    )
    assert posted["headers"] == {"Idempotency-Key": "c1", "X-Store-Id": "413"}


def test_native_tool_without_principal_headers_unchanged(monkeypatch):
    # No resolver configured: principal adds no headers (native tools keep working).
    posted = _native_tool_post(
        monkeypatch,
        WorkerContext(tool_urls={"h": "http://tools.local/h"}),
        CallToolInput(
            tool_ref={"kind": "native", "name": "h"}, value=1, cid="c2",
            principal=PRINCIPAL,
        ),
    )
    assert posted["headers"] == {"Idempotency-Key": "c2"}

    # Resolver configured but no principal on the run: nothing to resolve.
    posted = _native_tool_post(
        monkeypatch,
        WorkerContext(
            tool_urls={"h": "http://tools.local/h"},
            principal_headers=lambda p: {"X-Store-Id": str(p["storeId"])},
        ),
        CallToolInput(tool_ref={"kind": "native", "name": "h"}, value=1, cid="c3"),
    )
    assert posted["headers"] == {"Idempotency-Key": "c3"}


# --------------------------------------------------------------------------- #
# In-memory path: InMemoryEnv carries the principal; interpret(principal=...)
# installs it.
# --------------------------------------------------------------------------- #
def test_inmemory_env_carries_principal():
    seen = {}

    def echo(v):
        seen["principal"] = env.principal
        return v

    env = InMemoryEnv({}, _emitter(), tools={"echo": echo}, principal=PRINCIPAL)
    out = asyncio.run(interpret(call(native("echo")), 5, env))
    assert out.value == 5
    assert seen["principal"] == PRINCIPAL


def test_interpret_keyword_installs_principal():
    seen = {}

    def echo(v):
        seen["principal"] = env.principal
        return v

    env = InMemoryEnv({}, _emitter(), tools={"echo": echo})
    assert env.principal is None
    asyncio.run(interpret(call(native("echo")), 5, env, principal=PRINCIPAL))
    assert seen["principal"] == PRINCIPAL


def test_resolve_subflow_returns_bundle_metadata():
    flow_json = ident().to_json()
    configure(WorkerContext(subflows={"child": {"flowJson": flow_json, "bundle": BUNDLE_REF}}))

    out = asyncio.run(resolveSubflow("child"))

    assert out["flowJson"] == flow_json
    assert out["bundle"] == BUNDLE_REF


# --------------------------------------------------------------------------- #
# Temporal env: the principal is stamped into every effect payload, inherited
# by children, and carried across continue-as-new in both workflows.
# --------------------------------------------------------------------------- #
if HAVE_TEMPORAL:
    from julep.execution import harness
    from julep.execution.harness import (
        AgentInput,
        AgentWorkflow,
        FlowInput,
        FlowWorkflow,
        _TemporalEnv,
    )
    from julep.execution.policy import ExecutionPolicy


class _Stop(Exception):
    """Raised by the fake continue_as_new to capture the next segment's input."""


def _temporal_env(principal):
    async def gate(value, cid, timeout_s):
        return value

    return _TemporalEnv(
        manifest={},
        emitter=_emitter(),
        session_id="sess",
        manifest_json={},
        policy=ExecutionPolicy(),
        gate_waiter=gate,
        principal=principal,
    )


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_temporal_env_stamps_principal_into_effect_payloads(monkeypatch):
    payloads = []

    async def fake_execute_activity(fn, payload, **kwargs):
        payloads.append(payload)
        if fn.__name__ == "compilePlan":
            return ident().to_json()
        return {"ok": True}

    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)
    env = _temporal_env(PRINCIPAL)

    asyncio.run(env.run_call(call(mcp("kb", "search")), {"q": "x"}, "cid-1"))
    asyncio.run(env.invoke_reasoner("b", 5, "cid-2", None))
    asyncio.run(env.compile_plan("planner", 5, "cid-3"))

    # invoke_reasoner records the resolved QoS tier via a resolveQoS activity
    # (also principal-stamped) before the sync invokeReasoner dispatch.
    tool = next(p for p in payloads if isinstance(p, CallToolInput))
    qos = next(p for p in payloads if isinstance(p, ResolveQoSInput))
    reasoner = next(p for p in payloads if isinstance(p, InvokeReasonerInput))
    plan = next(p for p in payloads if isinstance(p, CompilePlanInput))
    assert tool.principal == PRINCIPAL
    assert qos.principal == PRINCIPAL
    assert reasoner.principal == PRINCIPAL
    assert plan.principal == PRINCIPAL


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_temporal_children_inherit_principal(monkeypatch):
    children = []

    async def fake_execute_child_workflow(fn, child_input, **kwargs):
        children.append(child_input)
        return "child-result"

    monkeypatch.setattr(harness.workflow, "execute_child_workflow", fake_execute_child_workflow)
    env = _temporal_env(PRINCIPAL)

    asyncio.run(env.run_sub("child", None, 5, "cid-1"))
    asyncio.run(env.run_agent("ctrl", 5, "cid-2"))

    sub_input, agent_input = children
    assert isinstance(sub_input, FlowInput) and sub_input.principal == PRINCIPAL
    assert isinstance(agent_input, AgentInput) and agent_input.principal == PRINCIPAL


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_temporal_ref_child_starts_with_child_bundle(monkeypatch):
    children = []

    async def fake_execute_activity(fn, payload, **kwargs):
        assert fn.__name__ == "resolveSubflow"
        assert payload == "child"
        return {"bundle": BUNDLE_REF}

    async def fake_execute_child_workflow(fn, child_input, **kwargs):
        children.append(child_input)
        return "child-result"

    monkeypatch.setattr(harness, "_bundle_ref_child_input_enabled", lambda: True)
    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)
    monkeypatch.setattr(harness.workflow, "execute_child_workflow", fake_execute_child_workflow)
    env = _temporal_env(PRINCIPAL)

    asyncio.run(env.run_sub("child", None, 5, "cid-1"))

    (sub_input,) = children
    assert isinstance(sub_input, FlowInput)
    assert sub_input.ref == "child"
    assert sub_input.bundle == BUNDLE_REF
    assert sub_input.principal == PRINCIPAL


def _always_continue(value):
    return continue_with({"n": value.get("n", 0) + 1})


register_pure("principal.always_continue", _always_continue)


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_flow_workflow_verify_pures_receives_bundle(monkeypatch):
    payloads = []

    async def fake_execute_activity(fn, payload, **kwargs):
        payloads.append((fn.__name__, payload))
        return None

    monkeypatch.setattr(harness, "_bundle_bound_verify_pures_enabled", lambda: True)
    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)

    inp = FlowInput(
        session_id="sess",
        input=5,
        flow_json=ident().to_json(),
        manifest_json={},
        pinned_pures={"bundle.worker.normalize.v1": "pure:abc"},
        max_call_limits={},
        bundle=BUNDLE_REF,
    )
    out = asyncio.run(FlowWorkflow().run(inp))

    verify_payloads = [payload for name, payload in payloads if name == "verifyPures"]
    assert out == 5
    assert verify_payloads == [
        VerifyPuresInput(pinned=inp.pinned_pures, bundle=BUNDLE_REF, flow_json=inp.flow_json)
    ]


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_flow_workflow_bundle_without_pins_still_verifies_binding(monkeypatch):
    payloads = []

    async def fake_execute_activity(fn, payload, **kwargs):
        payloads.append((fn.__name__, payload))
        return None

    monkeypatch.setattr(harness, "_bundle_bound_verify_pures_enabled", lambda: True)
    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)

    inp = FlowInput(
        session_id="sess",
        input=5,
        flow_json=ident().to_json(),
        manifest_json={},
        max_call_limits={},
        bundle=BUNDLE_REF,
    )
    out = asyncio.run(FlowWorkflow().run(inp))

    verify_payloads = [payload for name, payload in payloads if name == "verifyPures"]
    assert out == 5
    assert verify_payloads == [
        VerifyPuresInput(pinned={}, bundle=BUNDLE_REF, flow_json=inp.flow_json)
    ]


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_flow_workflow_continue_as_new_carries_principal(monkeypatch):
    captured = []

    def fake_continue_as_new(next_input):
        captured.append(next_input)
        raise _Stop()

    monkeypatch.setattr(harness.workflow, "continue_as_new", fake_continue_as_new)

    from julep import arr

    inp = FlowInput(
        session_id="sess",
        input={"n": 0},
        flow_json=arr("principal.always_continue").to_json(),
        manifest_json={},
        max_call_limits={},
        principal=PRINCIPAL,
        bundle=BUNDLE_REF,
    )
    with pytest.raises(_Stop):
        asyncio.run(FlowWorkflow().run(inp))

    (next_input,) = captured
    assert isinstance(next_input, FlowInput)
    # A segment restarting with principal=None when the run had one is a bug.
    assert next_input.principal == PRINCIPAL
    assert next_input.bundle == BUNDLE_REF
    assert next_input.input == {"n": 1}


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_agent_sub_child_starts_with_child_bundle(monkeypatch):
    children = []

    async def fake_execute_activity(fn, payload, **kwargs):
        if fn.__name__ == "invokeReasoner":
            return {"sub": "child", "input": 1}
        if fn.__name__ == "resolveSubflow":
            assert payload == "child"
            return {"bundle": BUNDLE_REF}
        raise AssertionError(f"unexpected activity {fn.__name__}")

    async def fake_execute_child_workflow(fn, child_input, **kwargs):
        children.append(child_input)
        return "child-result"

    monkeypatch.setattr(harness, "_bundle_ref_child_input_enabled", lambda: True)
    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)
    monkeypatch.setattr(harness.workflow, "execute_child_workflow", fake_execute_child_workflow)

    inp = AgentInput(
        controller="ctrl",
        session_id="sess",
        input=5,
        config={"maxRounds": 1, "budget": {"cost": 1000}},
        granted_subflows=["child"],
        resolve_spec=False,
        principal=PRINCIPAL,
    )
    out = asyncio.run(AgentWorkflow().run(inp))

    assert out["status"] == "max_rounds"
    (sub_input,) = children
    assert isinstance(sub_input, FlowInput)
    assert sub_input.ref == "child"
    assert sub_input.bundle == BUNDLE_REF
    assert sub_input.principal == PRINCIPAL


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_agent_workflow_continue_as_new_carries_principal(monkeypatch):
    captured = []
    payloads = []

    async def fake_execute_activity(fn, payload, **kwargs):
        if fn.__name__ not in {"startTrajectory", "finishTrajectory"}:
            payloads.append(payload)
        if fn.__name__ == "invokeReasoner":
            return {"tool": "t", "input": 1}
        return {"tool": "out"}

    def fake_continue_as_new(next_input):
        captured.append(next_input)
        raise _Stop()

    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)
    monkeypatch.setattr(harness.workflow, "continue_as_new", fake_continue_as_new)

    inp = AgentInput(
        controller="ctrl",
        session_id="sess",
        input=5,
        config={"maxRounds": 5, "budget": {"cost": 1000}, "continueAsNewAfter": 1},
        resolve_spec=False,
        principal=PRINCIPAL,
    )
    with pytest.raises(_Stop):
        asyncio.run(AgentWorkflow().run(inp))

    (next_input,) = captured
    assert isinstance(next_input, AgentInput)
    assert next_input.principal == PRINCIPAL
    # The round's effect payloads carried it too.
    assert all(p.principal == PRINCIPAL for p in payloads)


# --------------------------------------------------------------------------- #
# DBOS backend: the env stamps the principal into step payloads; the agent
# continuation envelope and the chaining runner carry it across segments.
# --------------------------------------------------------------------------- #
if HAVE_DBOS:
    from julep.continuation import CONTINUATION_KEY
    from julep.execution import dbos_backend
    from julep.execution.dbos_backend import (
        DbosEnv,
        decode_policy_error,
        encode_policy_error,
        run_flow_dbos,
    )
    from julep.execution.policy import ExecutionPolicy as _Policy


def _patch_dbos_steps(monkeypatch, payloads, *, reasoner_reply=None, plan_reply=None):
    async def fake_tool(inp: dict) -> Any:
        payloads.append(inp)
        return {"tool": "out"}

    async def fake_reasoner(inp: dict) -> Any:
        payloads.append(inp)
        return reasoner_reply if reasoner_reply is not None else {"reasoner": "out"}

    async def fake_plan(inp: dict) -> Any:
        payloads.append(inp)
        return plan_reply if plan_reply is not None else ident().to_json()

    monkeypatch.setattr(dbos_backend, "callToolIdempotent", fake_tool)
    monkeypatch.setattr(dbos_backend, "callToolNoRetry", fake_tool)
    monkeypatch.setattr(dbos_backend, "invokeReasonerStep", fake_reasoner)
    monkeypatch.setattr(dbos_backend, "compilePlanStep", fake_plan)


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_env_stamps_principal_into_step_payloads(monkeypatch):
    payloads: list[dict] = []
    _patch_dbos_steps(monkeypatch, payloads)

    env = DbosEnv(
        manifest={},
        emitter=_emitter(),
        session_id="sess",
        manifest_json={},
        policy=_Policy(),
        principal=PRINCIPAL,
    )
    asyncio.run(env.run_call(call(mcp("kb", "search")), {"q": "x"}, "cid-1"))
    asyncio.run(env.invoke_reasoner("b", 5, "cid-2", None))
    asyncio.run(env.compile_plan("planner", 5, "cid-3"))

    assert len(payloads) == 3
    assert all(p["principal"] == PRINCIPAL for p in payloads)


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_inline_subflow_inherits_principal(monkeypatch):
    payloads: list[dict] = []
    _patch_dbos_steps(monkeypatch, payloads)

    async def fake_resolve(ref: str) -> dict:
        return {"flowJson": call(mcp("kb", "search")).to_json(), "manifestJson": {}}

    monkeypatch.setattr(dbos_backend, "resolveSubflowStep", fake_resolve)

    env = DbosEnv(
        manifest={},
        emitter=_emitter(),
        session_id="sess",
        manifest_json={},
        policy=_Policy(),
        principal=PRINCIPAL,
    )
    out = asyncio.run(env.run_sub("child", None, 5, "cid-1"))
    assert out == {"tool": "out"}
    (child_payload,) = payloads
    assert child_payload["principal"] == PRINCIPAL


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_inline_subflow_verifies_with_bundle(monkeypatch):
    verify_payloads = []
    flow_json = ident().to_json()

    async def fake_resolve(ref: str) -> dict:
        return {
            "flowJson": flow_json,
            "manifestJson": {},
            "pinnedPures": {"bundle.worker.normalize.v1": "pure:abc"},
            "bundle": BUNDLE_REF,
        }

    async def fake_verify(inp):
        verify_payloads.append(inp)
        return None

    monkeypatch.setattr(dbos_backend, "resolveSubflowStep", fake_resolve)
    monkeypatch.setattr(dbos_backend, "verifyPuresStep", fake_verify)

    env = DbosEnv(
        manifest={},
        emitter=_emitter(),
        session_id="sess",
        manifest_json={},
        policy=_Policy(),
    )
    out = asyncio.run(env.run_sub("child", None, 5, "cid-1"))

    assert out == 5
    assert verify_payloads == [
        VerifyPuresInput(
            pinned={"bundle.worker.normalize.v1": "pure:abc"},
            bundle=BUNDLE_REF,
            flow_json=flow_json,
        )
    ]


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_agent_segment_envelope_carries_principal(monkeypatch):
    payloads: list[dict] = []
    _patch_dbos_steps(monkeypatch, payloads, reasoner_reply={"tool": "t", "input": 1})

    # The raw (undecorated) workflow body: same code, no DBOS runtime needed.
    agent_body = inspect.unwrap(dbos_backend.agent_workflow)
    out = asyncio.run(agent_body({
        "controller": "ctrl",
        "sessionId": "sess",
        "input": 5,
        "config": {"maxRounds": 5, "budget": {"cost": 1000}, "continueAsNewAfter": 1},
        "resolveSpec": False,
        "principal": PRINCIPAL,
    }))

    # One completed CALL round -> continuation envelope for the next segment.
    assert CONTINUATION_KEY in out
    assert out[CONTINUATION_KEY]["principal"] == PRINCIPAL
    assert all(p["principal"] == PRINCIPAL for p in payloads)


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_flow_segment_threads_principal(monkeypatch):
    payloads: list[dict] = []
    _patch_dbos_steps(monkeypatch, payloads)

    flow_body = inspect.unwrap(dbos_backend.flow_workflow)
    out = asyncio.run(flow_body({
        "sessionId": "sess",
        "input": 5,
        "flowJson": call(mcp("kb", "search")).to_json(),
        "manifestJson": {},
        "maxCallLimits": {},
        "principal": PRINCIPAL,
    }))
    assert out == {"tool": "out"}
    (payload,) = payloads
    assert payload["principal"] == PRINCIPAL


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_flow_segment_verifies_with_bundle(monkeypatch):
    verify_payloads = []
    flow_json = ident().to_json()

    async def fake_verify(inp):
        verify_payloads.append(inp)
        return None

    monkeypatch.setattr(dbos_backend, "verifyPuresStep", fake_verify)

    flow_body = inspect.unwrap(dbos_backend.flow_workflow)
    out = asyncio.run(flow_body({
        "sessionId": "sess",
        "input": 5,
        "flowJson": flow_json,
        "manifestJson": {},
        "pinnedPures": {"bundle.worker.normalize.v1": "pure:abc"},
        "maxCallLimits": {},
        "bundle": BUNDLE_REF,
    }))

    assert out == 5
    assert verify_payloads == [
        VerifyPuresInput(
            pinned={"bundle.worker.normalize.v1": "pure:abc"},
            bundle=BUNDLE_REF,
            flow_json=flow_json,
        )
    ]


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_ref_flow_adopts_bundle_for_verify(monkeypatch):
    verify_payloads = []
    flow_json = ident().to_json()

    async def fake_resolve(ref: str) -> dict:
        assert ref == "child"
        return {
            "flowJson": flow_json,
            "manifestJson": {},
            "pinnedPures": {"bundle.worker.normalize.v1": "pure:abc"},
            "bundle": BUNDLE_REF,
        }

    async def fake_verify(inp):
        verify_payloads.append(inp)
        return None

    monkeypatch.setattr(dbos_backend, "resolveSubflowStep", fake_resolve)
    monkeypatch.setattr(dbos_backend, "verifyPuresStep", fake_verify)

    flow_body = inspect.unwrap(dbos_backend.flow_workflow)
    out = asyncio.run(flow_body({
        "sessionId": "sess",
        "input": 5,
        "ref": "child",
        "maxCallLimits": {},
    }))

    assert out == 5
    assert verify_payloads == [
        VerifyPuresInput(
            pinned={"bundle.worker.normalize.v1": "pure:abc"},
            bundle=BUNDLE_REF,
            flow_json=flow_json,
        )
    ]


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_chain_runner_carries_principal_to_every_segment(monkeypatch):
    submitted: list[dict] = []
    results = iter([
        {CONTINUATION_KEY: {"n": 1}, "callCounts": {}},
        {"done": 1},
    ])

    class _Handle:
        async def get_result(self):
            return next(results)

    class _FakeDBOS:
        @staticmethod
        async def start_workflow_async(fn, payload):
            submitted.append(payload)
            return _Handle()

    class _NoopSetWorkflowID:
        def __init__(self, wfid):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(dbos_backend, "DBOS", _FakeDBOS)
    monkeypatch.setattr(dbos_backend, "SetWorkflowID", _NoopSetWorkflowID)

    out = asyncio.run(run_flow_dbos(
        ident().to_json(),
        {},
        session_id="sess",
        input={"n": 0},
        principal=PRINCIPAL,
        bundle=BUNDLE_REF,
    ))
    assert out == {"done": 1}
    assert len(submitted) == 2
    # Both segments — including the one restarted from a continuation — carry it.
    assert all(p["principal"] == PRINCIPAL for p in submitted)
    assert all(p["bundle"] == BUNDLE_REF for p in submitted)


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_principal_required_is_a_dbos_policy_error():
    env = encode_policy_error(PrincipalRequired("worker requires a principal"))
    with pytest.raises(PrincipalRequired, match="requires a principal"):
        decode_policy_error(env)
