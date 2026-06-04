"""End-to-end tests against Temporal's time-skipping test server.

Skipped entirely when ``temporalio`` is not installed. All four verified flows
run inside a single :class:`WorkflowEnvironment` (one server start, amortized)
driven by a synchronous wrapper, so the module needs no pytest-asyncio config.

Effect handlers are injected in-process callables (an MCP caller and an LLM), so
no HTTP hand server is required; native hands would need one.
"""

from __future__ import annotations

import asyncio
import uuid

import pytest

from composable_agents import HAVE_TEMPORAL

pytestmark = pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")

if HAVE_TEMPORAL:
    from temporalio.client import WorkflowFailureError
    from temporalio.exceptions import ApplicationError
    from temporalio.testing import WorkflowEnvironment

    from composable_agents import (
        call, mcp, seq, think, freeze, manifest_to_json,
        arr,
        register_brain, Brain,
    )
    from composable_agents.derived import race, human_gate
    from composable_agents.freeze import (
        McpSnapshot, McpServerSnapshot, McpToolSpec,
    )
    from composable_agents.contracts import McpAnnotations
    from composable_agents.execution.harness import (
        run_flow, start_flow, AgentWorkflow, AgentInput, ExecutionPolicy,
    )
    from composable_agents.execution.worker import build_worker
    from composable_agents.execution.activities import WorkerContext
    from composable_agents import purity
    from composable_agents.purity import PureEntry
    from composable_agents.deploy import deploy
    from composable_agents.errors import PureDriftError


# --------------------------------------------------------------------------- #
# In-process tool + brain fakes.
# --------------------------------------------------------------------------- #
def _snapshot():
    ann = McpAnnotations(read_only_hint=True, idempotent_hint=True)
    return McpSnapshot(servers={"srv": McpServerSnapshot(server="srv", version="1", tools={
        t: McpToolSpec(input_schema={}, annotations=ann)
        for t in ("double", "inc", "echo", "fail", "slow")
    })})


async def _mcp(server, tool, value, idempotency_key):
    assert idempotency_key
    if tool == "double":
        return value * 2
    if tool == "inc":
        return value + 1
    if tool == "echo":
        return value
    if tool == "fail":
        raise RuntimeError("intentional race failure")
    if tool == "slow":
        await asyncio.sleep(5)  # time-skipped by the server
        return value * 100
    raise ValueError(tool)


def _drift_pure(value):
    return value


async def _llm(brain, value):
    if brain.name == "adder":
        return value + 10
    if brain.name == "ctrl":
        n = len(value.get("trace", []))
        if n == 0:
            return {"tool": "srv/double", "input": value["input"]}
        if n == 1:
            return {"sub": "child"}
        return {"done": True, "output": value["input"]}
    return value


def _child_registry():
    fr = freeze(call(mcp("srv", "inc")), _snapshot())
    return {"child": {"flowJson": fr.flow.to_json(), "manifestJson": manifest_to_json(fr.manifest)}}


def _worker(env, *, task_queue, agents=None, llm=None, extra_brains=(), mcp_call=None):
    register_brain(Brain(name="adder", model="test", system="add 10"))
    register_brain(Brain(name="ctrl", model="test", system="decide"))
    for brain in extra_brains:
        register_brain(brain)
    ctx = WorkerContext(
        mcp_call=mcp_call or _mcp,
        llm=llm or _llm,
        subflows=_child_registry(),
        agents=agents or {},
    )
    return build_worker(env.client, ctx, task_queue=task_queue)


# --------------------------------------------------------------------------- #
# Scenarios (each returns nothing; raises on failure).
# --------------------------------------------------------------------------- #
async def _pipeline_and_brain(env):
    fr = freeze(seq(call(mcp("srv", "double")), think("adder")), _snapshot())
    async with _worker(env, task_queue="ca-pipe"):
        out = await run_flow(env.client, fr.flow.to_json(), manifest_to_json(fr.manifest),
                             session_id=f"pipe-{uuid.uuid4()}", input=5, task_queue="ca-pipe")
    assert out == 20, f"pipeline+brain expected 20, got {out}"


async def _race(env):
    fr = freeze(race(call(mcp("srv", "fail")), call(mcp("srv", "slow"))), _snapshot())
    async with _worker(env, task_queue="ca-race"):
        out = await run_flow(env.client, fr.flow.to_json(), manifest_to_json(fr.manifest),
                             session_id=f"race-{uuid.uuid4()}", input=7, task_queue="ca-race",
                             policy=ExecutionPolicy(idempotent_max_attempts=1))
    assert out == 700, f"race expected slow success 700 after fast failure, got {out}"


async def _human_gate(env):
    fr = freeze(seq(human_gate(timeout_s=None), call(mcp("srv", "echo"))), _snapshot())
    async with _worker(env, task_queue="ca-gate"):
        sid = f"gate-{uuid.uuid4()}"
        handle = await start_flow(env.client, fr.flow.to_json(), manifest_to_json(fr.manifest),
                                  session_id=sid, input={"q": "x"}, task_queue="ca-gate")
        cid = None
        for _ in range(60):
            gates = await handle.query("openGates")
            if gates:
                cid = gates[0]
                break
            await asyncio.sleep(0.1)
        assert cid is not None, "human gate never opened"
        await handle.signal("submitHuman", {"cid": cid, "value": {"approved": True, "n": 99}})
        out = await handle.result()
    assert out == {"approved": True, "n": 99}, f"gate value did not flow through: {out}"


async def _agent(env):
    agents = {"ctrl": {"config": {"maxRounds": 6, "budget": {"usd": 1000}}, "grantedTools": ["srv/double"]}}
    async with _worker(env, task_queue="ca-agent", agents=agents):
        sid = f"agent-{uuid.uuid4()}"
        res = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(controller="ctrl", session_id=sid, input=5, policy=ExecutionPolicy().to_json()),
            id=sid, task_queue="ca-agent",
        )
    assert res["status"] == "done", res
    assert res["output"] == 11, f"agent expected 11, got {res['output']}"
    assert [t["decision"] for t in res["trace"]] == ["call", "sub"], res

    # Budget guard: a budget below the per-round think cost trips over_budget.
    budget_brain_calls = {"count": 0}

    async def fail_if_budget_brain_invoked(brain, value):  # noqa: ANN001
        budget_brain_calls["count"] += 1
        raise RuntimeError("budget controller should not be invoked")

    agents_b = {
        "budget_ctrl": {
            "config": {"maxRounds": 6, "budget": {"usd": 0.5}},
            "grantedTools": ["srv/double"],
        }
    }
    async with _worker(
        env,
        task_queue="ca-agent-b",
        agents=agents_b,
        llm=fail_if_budget_brain_invoked,
        extra_brains=(Brain(name="budget_ctrl", model="test", system="budget"),),
    ):
        sid = f"agentb-{uuid.uuid4()}"
        res2 = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(
                controller="budget_ctrl",
                session_id=sid,
                input=5,
                policy=ExecutionPolicy().to_json(),
            ),
            id=sid, task_queue="ca-agent-b",
        )
    assert res2["status"] == "over_budget", res2
    assert res2["spentUsd"] == 0, res2
    assert res2["trace"] == [], res2
    assert budget_brain_calls["count"] == 0

    # Capability deny: the requested tool is not granted.
    agents_d = {"ctrl": {"config": {"maxRounds": 6, "budget": {"usd": 1000}}, "grantedTools": ["only/other"]}}
    async with _worker(env, task_queue="ca-agent-d", agents=agents_d):
        sid = f"agentd-{uuid.uuid4()}"
        res3 = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(controller="ctrl", session_id=sid, input=5, policy=ExecutionPolicy().to_json()),
            id=sid, task_queue="ca-agent-d",
        )
    assert res3["status"] == "denied", res3

    # Agent loops cannot open a human approval gate, so approval-required tools deny.
    agents_a = {
        "ctrl": {
            "config": {"maxRounds": 6, "budget": {"usd": 1000}},
            "grantedTools": ["srv/double"],
            "grantedContracts": {
                "srv/double": {
                    "effect": "read",
                    "idempotency": "native",
                    "approval": True,
                }
            },
        }
    }
    async with _worker(env, task_queue="ca-agent-a", agents=agents_a):
        sid = f"agenta-{uuid.uuid4()}"
        res4 = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(controller="ctrl", session_id=sid, input=5, policy=ExecutionPolicy().to_json()),
            id=sid, task_queue="ca-agent-a",
        )
    assert res4["status"] == "denied", res4
    assert res4["reason"] == "approval-required tool 'srv/double'; agent must ESCALATE"

    # maxCalls: the per-tool counter is carried through continue-as-new and
    # denies the second requested call before dispatching another effect.
    max_call_effects = {"count": 0}

    async def counted_mcp(server, tool, value, idempotency_key):  # noqa: ANN001
        max_call_effects["count"] += 1
        return await _mcp(server, tool, value, idempotency_key)

    async def max_calls_llm(brain, value):  # noqa: ANN001
        if brain.name == "max_ctrl":
            return {"tool": "srv/double", "input": value["input"]}
        return await _llm(brain, value)

    agents_m = {
        "max_ctrl": {
            "config": {
                "maxRounds": 6,
                "budget": {"usd": 1000},
                "continueAsNewAfter": 1,
            },
            "grantedTools": ["srv/double"],
            "grantedContracts": {
                "srv/double": {
                    "effect": "read",
                    "idempotency": "native",
                    "maxCalls": 1,
                }
            },
        }
    }
    async with _worker(
        env,
        task_queue="ca-agent-m",
        agents=agents_m,
        llm=max_calls_llm,
        mcp_call=counted_mcp,
        extra_brains=(Brain(name="max_ctrl", model="test", system="max calls"),),
    ):
        sid = f"agentm-{uuid.uuid4()}"
        res5 = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(controller="max_ctrl", session_id=sid, input=5, policy=ExecutionPolicy().to_json()),
            id=sid,
            task_queue="ca-agent-m",
        )
    assert res5["status"] == "denied", res5
    assert res5["reason"] == "tool 'srv/double' exceeded maxCalls=1"
    assert [t["decision"] for t in res5["trace"]] == ["call"], res5
    assert max_call_effects["count"] == 1

    # Subflow grants: None is unconstrained, [] denies all, and a listed child
    # is allowed through the agent SUB path.
    async def subflow_llm(brain, value):  # noqa: ANN001
        if brain.name.startswith("sub_ctrl_"):
            if not value.get("trace"):
                return {"sub": "child", "input": value["input"]}
            return {"done": True, "output": value["input"]}
        return await _llm(brain, value)

    sub_agents = {
        "sub_ctrl_denied": {
            "config": {"maxRounds": 3, "budget": {"usd": 1000}},
            "grantedSubflows": ["other"],
        },
        "sub_ctrl_empty": {
            "config": {"maxRounds": 3, "budget": {"usd": 1000}},
            "grantedSubflows": [],
        },
        "sub_ctrl_allowed": {
            "config": {"maxRounds": 3, "budget": {"usd": 1000}},
            "grantedSubflows": ["child"],
        },
    }
    async with _worker(
        env,
        task_queue="ca-agent-sub",
        agents=sub_agents,
        llm=subflow_llm,
        extra_brains=(
            Brain(name="sub_ctrl_denied", model="test", system="sub denied"),
            Brain(name="sub_ctrl_empty", model="test", system="sub empty"),
            Brain(name="sub_ctrl_allowed", model="test", system="sub allowed"),
        ),
    ):
        denied = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(
                controller="sub_ctrl_denied",
                session_id=f"agentsubd-{uuid.uuid4()}",
                input=5,
                policy=ExecutionPolicy().to_json(),
            ),
            id=f"agentsubd-{uuid.uuid4()}",
            task_queue="ca-agent-sub",
        )
        empty = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(
                controller="sub_ctrl_empty",
                session_id=f"agentsube-{uuid.uuid4()}",
                input=5,
                policy=ExecutionPolicy().to_json(),
            ),
            id=f"agentsube-{uuid.uuid4()}",
            task_queue="ca-agent-sub",
        )
        allowed = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(
                controller="sub_ctrl_allowed",
                session_id=f"agentsuba-{uuid.uuid4()}",
                input=5,
                policy=ExecutionPolicy().to_json(),
            ),
            id=f"agentsuba-{uuid.uuid4()}",
            task_queue="ca-agent-sub",
        )
    assert denied["status"] == "denied", denied
    assert denied["reason"] == "subflow 'child' is not granted"
    assert denied["trace"] == []
    assert empty["status"] == "denied", empty
    assert empty["reason"] == "subflow 'child' is not granted"
    assert allowed["status"] == "done", allowed
    assert allowed["output"] == 6, allowed
    assert [t["decision"] for t in allowed["trace"]] == ["sub"], allowed


async def _pure_drift_fails_before_effect(env):
    effects = {"count": 0}

    async def mcp_counter(server, tool, value, idempotency_key):  # noqa: ANN001
        effects["count"] += 1
        return await _mcp(server, tool, value, idempotency_key)

    purity._REGISTRY["e2e.drift"] = PureEntry("e2e.drift", _drift_pure, "pure:pinned")
    deployment = deploy(seq(arr("e2e.drift"), call(mcp("srv", "inc"))), _snapshot())
    purity._REGISTRY["e2e.drift"] = PureEntry("e2e.drift", _drift_pure, "pure:changed")

    ctx = WorkerContext(mcp_call=mcp_counter, llm=_llm, subflows=_child_registry())
    async with build_worker(env.client, ctx, task_queue="ca-pure-drift"):
        with pytest.raises(WorkflowFailureError) as raised:
            await deployment.run(
                env.client,
                session_id=f"pure-drift-{uuid.uuid4()}",
                input=5,
                task_queue="ca-pure-drift",
            )

    cause = raised.value.__cause__
    while cause is not None and not (
        isinstance(cause, ApplicationError) and cause.type == PureDriftError.__name__
    ):
        cause = cause.__cause__

    assert isinstance(cause, ApplicationError)
    assert cause.type == PureDriftError.__name__
    assert "e2e.drift" in str(cause)
    assert effects["count"] == 0


async def _run_all():
    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _pipeline_and_brain(env)
        await _race(env)
        await _human_gate(env)
        await _agent(env)
        await _pure_drift_fails_before_effect(env)


def test_temporal_end_to_end():
    """Run all E2E flows in one time-skipping environment."""
    asyncio.run(asyncio.wait_for(_run_all(), timeout=180))
