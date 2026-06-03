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
    from temporalio.testing import WorkflowEnvironment

    from composable_agents import (
        mcp_call, pipeline, think, freeze, manifest_to_json,
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


# --------------------------------------------------------------------------- #
# In-process tool + brain fakes.
# --------------------------------------------------------------------------- #
def _snapshot():
    ann = McpAnnotations(read_only_hint=True, idempotent_hint=True)
    return McpSnapshot(servers={"srv": McpServerSnapshot(server="srv", version="1", tools={
        t: McpToolSpec(input_schema={}, annotations=ann)
        for t in ("double", "inc", "echo", "slow")
    })})


async def _mcp(server, tool, value):
    if tool == "double":
        return value * 2
    if tool == "inc":
        return value + 1
    if tool == "echo":
        return value
    if tool == "slow":
        await asyncio.sleep(5)  # time-skipped by the server
        return value * 100
    raise ValueError(tool)


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
    fr = freeze(mcp_call("srv", "inc"), _snapshot())
    return {"child": {"flowJson": fr.flow.to_json(), "manifestJson": manifest_to_json(fr.manifest)}}


def _worker(env, *, task_queue, agents=None):
    register_brain(Brain(name="adder", model="test", system_prompt="add 10"))
    register_brain(Brain(name="ctrl", model="test", system_prompt="decide"))
    ctx = WorkerContext(mcp_call=_mcp, llm=_llm, subflows=_child_registry(), agents=agents or {})
    return build_worker(env.client, ctx, task_queue=task_queue)


# --------------------------------------------------------------------------- #
# Scenarios (each returns nothing; raises on failure).
# --------------------------------------------------------------------------- #
async def _pipeline_and_brain(env):
    fr = freeze(pipeline(mcp_call("srv", "double"), think("adder")), _snapshot())
    async with _worker(env, task_queue="ca-pipe"):
        out = await run_flow(env.client, fr.flow.to_json(), manifest_to_json(fr.manifest),
                             session_id=f"pipe-{uuid.uuid4()}", input=5, task_queue="ca-pipe")
    assert out == 20, f"pipeline+brain expected 20, got {out}"


async def _race(env):
    fr = freeze(race(mcp_call("srv", "inc"), mcp_call("srv", "slow")), _snapshot())
    async with _worker(env, task_queue="ca-race"):
        out = await run_flow(env.client, fr.flow.to_json(), manifest_to_json(fr.manifest),
                             session_id=f"race-{uuid.uuid4()}", input=7, task_queue="ca-race")
    assert out == 8, f"race expected fast branch 8, got {out}"


async def _human_gate(env):
    fr = freeze(pipeline(human_gate(timeout_s=None), mcp_call("srv", "echo")), _snapshot())
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
    agents_b = {"ctrl": {"config": {"maxRounds": 6, "budget": {"usd": 0.5}}, "grantedTools": ["srv/double"]}}
    async with _worker(env, task_queue="ca-agent-b", agents=agents_b):
        sid = f"agentb-{uuid.uuid4()}"
        res2 = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(controller="ctrl", session_id=sid, input=5, policy=ExecutionPolicy().to_json()),
            id=sid, task_queue="ca-agent-b",
        )
    assert res2["status"] == "over_budget", res2

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


async def _run_all():
    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _pipeline_and_brain(env)
        await _race(env)
        await _human_gate(env)
        await _agent(env)


def test_temporal_end_to_end():
    """Run all E2E flows in one time-skipping environment."""
    asyncio.run(asyncio.wait_for(_run_all(), timeout=180))
