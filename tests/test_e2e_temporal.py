"""End-to-end tests against Temporal's time-skipping test server.

Skipped entirely when ``temporalio`` is not installed. All four verified flows
run inside a single :class:`WorkflowEnvironment` (one server start, amortized)
driven by a synchronous wrapper, so the module needs no pytest-asyncio config.

Effect handlers are injected in-process callables (an MCP caller and an LLM), so
no HTTP tool server is required; native tools would need one.
"""

from __future__ import annotations

import asyncio
import json
import uuid

import pytest

from julep import HAVE_TEMPORAL

pytestmark = pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")

if HAVE_TEMPORAL:
    from temporalio.client import WorkflowFailureError
    from temporalio.exceptions import ApplicationError
    from temporalio.testing import WorkflowEnvironment

    from julep import (
        call, mcp, seq, think, freeze, manifest_to_json,
        arr,
        Reasoner,
        app,
        Budget,
        CapabilityManifest,
        Contract,
        sub,
    )
    from julep.derived import race, human_gate
    from julep.freeze import (
        McpSnapshot, McpServerSnapshot, McpToolSpec,
    )
    from julep.contracts import McpAnnotations
    from julep.execution.harness import (
        run_flow, start_flow, AgentWorkflow, AgentInput, ExecutionPolicy,
    )
    from julep.agent_loop import (
        REQUIRE_TOOL_CALL_NEVER_CALLED_REASON,
        REQUIRE_TOOL_CALL_REASK_MESSAGE,
    )
    from julep.execution.worker import build_worker, WORKFLOWS, ACTIVITIES
    from julep.execution.activities import (
        WorkerContext, configure,
    )
    from julep.execution.session_store import InMemorySessionStore
    from julep.execution.blobstore import InMemoryBlobStore
    from julep.execution.llm_result import LlmCallMeta, LlmResult
    from temporalio.worker import Worker
    from julep import purity
    from julep.purity import PureEntry
    from julep.deploy import deploy
    from julep.errors import PureDriftError
    from julep.registry import DEFAULT_REGISTRY


# --------------------------------------------------------------------------- #
# In-process tool + reasoner fakes.
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


async def _llm(reasoner, value):
    if reasoner.name == "adder":
        return value + 10
    if reasoner.name == "ctrl":
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


def _worker(env, *, task_queue, agents=None, llm=None, extra_reasoners=(), mcp_call=None):
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="adder", model="test", system="add 10"))
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="ctrl", model="test", system="decide"))
    for reasoner in extra_reasoners:
        DEFAULT_REGISTRY.register_reasoner(reasoner)
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
async def _pipeline_and_reasoner(env):
    fr = freeze(seq(call(mcp("srv", "double")), think("adder")), _snapshot())
    async with _worker(env, task_queue="julep-pipe"):
        out = await run_flow(env.client, fr.flow.to_json(), manifest_to_json(fr.manifest),
                             session_id=f"pipe-{uuid.uuid4()}", input=5, task_queue="julep-pipe")
    assert out == 20, f"pipeline+reasoner expected 20, got {out}"


async def _queue_lanes_do_not_break_subflow_inheritance(env):
    fr = freeze(sub("child", Contract.pipeline()), _snapshot())
    async with _worker(env, task_queue="julep-queue-lanes"):
        out = await run_flow(
            env.client,
            fr.flow.to_json(),
            manifest_to_json(fr.manifest),
            session_id=f"queue-lanes-{uuid.uuid4()}",
            input=5,
            task_queue="julep-queue-lanes",
            queue_lanes={"foreground": "julep-fg"},
        )
    assert out == 6, f"queue-lane subflow expected 6, got {out}"


async def _agent_sub_routes_to_mapped_lane(env):
    """A durable agent SUB routes the child onto a mapped lane, end-to-end.

    Teeth: the lane worker's mcp returns inc(x)=x+1000 while the parent worker's
    returns x+1. The child is ref-only, so it runs wherever it is STARTED; the
    parent AgentWorkflow's SUB start must set task_queue=<mapped lane> for the
    child to land on the lane worker. output==1005 proves the child ran on the
    lane worker (inc(5)+1000); a routing regression would inherit the parent
    queue and yield 6. This exercises the full carrier:
    APP-node subflowQueues -> _app_config -> run_agent -> AgentInput.subflow_queues
    -> _resolve_child_queue -> execute_child_workflow(task_queue=mapped).
    """
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="lane_ctrl", model="test", system="decide"))
    parent_q, lane_q = "julep-lane-parent", "julep-lane-bg"

    async def lane_mcp(server, tool, value, idempotency_key):
        assert idempotency_key
        if tool == "inc":
            return value + 1000
        return await _mcp(server, tool, value, idempotency_key)

    async def lane_llm(reasoner, value):
        if reasoner.name == "lane_ctrl":
            if not value.get("trace"):
                return {"sub": "child", "input": value["input"]}
            return {"done": True, "output": value["input"]}
        return await _llm(reasoner, value)

    # Hand-built APP node carrying subflowQueues (identical shape to what
    # Agent(tools=[child.as_sub(queue="background")]) now produces).
    parent_flow = app(
        "lane_ctrl",
        subflows=["child"],
        subflow_queues={"child": "background"},
        budget=Budget(cost=1000),
        max_rounds=4,
    )
    fr = freeze(parent_flow, _snapshot())

    # Both workers register "child": the parent worker resolves the ref for the
    # bundle-child-input activity; the lane worker runs it. Only the mcp differs.
    parent_ctx = WorkerContext(mcp_call=_mcp, llm=lane_llm, subflows=_child_registry())
    lane_ctx = WorkerContext(mcp_call=lane_mcp, llm=lane_llm, subflows=_child_registry())
    async with build_worker(env.client, parent_ctx, task_queue=parent_q), \
               build_worker(env.client, lane_ctx, task_queue=lane_q):
        out = await run_flow(
            env.client,
            fr.flow.to_json(),
            manifest_to_json(fr.manifest),
            session_id=f"lane-{uuid.uuid4()}",
            input=5,
            task_queue=parent_q,
            queue_lanes={"background": lane_q},
        )
    assert out["status"] == "done", out
    assert out["output"] == 1005, (
        f"agent SUB must route the child onto the mapped lane worker "
        f"(inc(5)+1000=1005); got {out['output']!r} - a routing regression "
        f"would inherit the parent queue and yield 6"
    )


async def _principal_threading(env):
    """Dispatch-supplied principal reaches a new-style MCP caller end-to-end."""
    seen = {}

    async def principal_mcp(server, tool, value, idempotency_key, principal):
        seen["principal"] = principal
        return await _mcp(server, tool, value, idempotency_key)

    fr = freeze(call(mcp("srv", "double")), _snapshot())
    async with _worker(env, task_queue="julep-principal", mcp_call=principal_mcp):
        out = await run_flow(
            env.client, fr.flow.to_json(), manifest_to_json(fr.manifest),
            session_id=f"principal-{uuid.uuid4()}", input=3, task_queue="julep-principal",
            principal={"storeId": 413, "tokenRef": "cred_abc"},
        )
    assert out == 6, f"principal flow expected 6, got {out}"
    assert seen["principal"] == {"storeId": 413, "tokenRef": "cred_abc"}, seen


async def _race(env):
    fr = freeze(race(call(mcp("srv", "fail")), call(mcp("srv", "slow"))), _snapshot())
    async with _worker(env, task_queue="julep-race"):
        out = await run_flow(env.client, fr.flow.to_json(), manifest_to_json(fr.manifest),
                             session_id=f"race-{uuid.uuid4()}", input=7, task_queue="julep-race",
                             policy=ExecutionPolicy(idempotent_max_attempts=1))
    assert out == 700, f"race expected slow success 700 after fast failure, got {out}"


async def _human_gate(env):
    fr = freeze(seq(human_gate(timeout_s=None), call(mcp("srv", "echo"))), _snapshot())
    async with _worker(env, task_queue="julep-gate"):
        sid = f"gate-{uuid.uuid4()}"
        handle = await start_flow(env.client, fr.flow.to_json(), manifest_to_json(fr.manifest),
                                  session_id=sid, input={"q": "x"}, task_queue="julep-gate")
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


async def _human_gate_timeout(env):
    fr = freeze(human_gate(timeout_s=1), _snapshot())
    async with _worker(env, task_queue="julep-gate-timeout"):
        out = await run_flow(
            env.client,
            fr.flow.to_json(),
            manifest_to_json(fr.manifest),
            session_id=f"gate-timeout-{uuid.uuid4()}",
            input={"q": "timeout"},
            task_queue="julep-gate-timeout",
        )
    assert out == {
        "approved": False,
        "reason": "timeout",
        "input": {"q": "timeout"},
    }, f"gate timeout lost original input: {out}"


async def _generic_worker_agent_loop(env):
    """A worker without a preloaded agent map runs an explicit AgentInput."""
    reasoner = Reasoner(name="generic_ctrl", model="test", system="decide")
    DEFAULT_REGISTRY.register_reasoner(reasoner)

    async def generic_llm(current, value):  # noqa: ANN001
        assert current.name == "generic_ctrl"
        if not value.get("trace"):
            return {"tool": "srv/double", "input": value["input"]}
        return {"done": True, "output": value["input"]}

    ctx = WorkerContext(mcp_call=_mcp, llm=generic_llm)
    async with build_worker(
        env.client,
        ctx,
        task_queue="julep-generic-agent",
    ):
        sid = f"generic-agent-{uuid.uuid4()}"
        result = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(
                controller="generic_ctrl",
                session_id=sid,
                input=5,
                config={"maxRounds": 3, "budget": {"cost": 1000}},
                granted_tools=["srv/double"],
                policy=ExecutionPolicy().to_json(),
                resolve_spec=False,
            ),
            id=sid,
            task_queue="julep-generic-agent",
        )

    assert result["status"] == "done", result
    assert result["output"] == 10, result
    assert [entry["decision"] for entry in result["trace"]] == ["call"]


async def _agent(env):
    agents = {"ctrl": {"config": {"maxRounds": 6, "budget": {"cost": 1000}}, "grantedTools": ["srv/double"]}}
    async with _worker(env, task_queue="julep-agent", agents=agents):
        sid = f"agent-{uuid.uuid4()}"
        res = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(controller="ctrl", session_id=sid, input=5, policy=ExecutionPolicy().to_json()),
            id=sid, task_queue="julep-agent",
        )
    assert res["status"] == "done", res
    assert res["output"] == 11, f"agent expected 11, got {res['output']}"
    assert [t["decision"] for t in res["trace"]] == ["call", "sub"], res

    # Budget guard: a budget below the per-round think cost trips over_budget.
    budget_reasoner_calls = {"count": 0}

    async def fail_if_budget_reasoner_invoked(reasoner, value):  # noqa: ANN001
        budget_reasoner_calls["count"] += 1
        raise RuntimeError("budget controller should not be invoked")

    agents_b = {
        "budget_ctrl": {
            "config": {"maxRounds": 6, "budget": {"cost": 0.5}},
            "grantedTools": ["srv/double"],
        }
    }
    async with _worker(
        env,
        task_queue="julep-agent-b",
        agents=agents_b,
        llm=fail_if_budget_reasoner_invoked,
        extra_reasoners=(Reasoner(name="budget_ctrl", model="test", system="budget"),),
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
            id=sid, task_queue="julep-agent-b",
        )
    assert res2["status"] == "over_budget", res2
    assert res2["cost"] == 0, res2
    assert res2["trace"] == [], res2
    assert budget_reasoner_calls["count"] == 0

    # Capability deny: the requested tool is not granted.
    agents_d = {"ctrl": {"config": {"maxRounds": 6, "budget": {"cost": 1000}}, "grantedTools": ["only/other"]}}
    async with _worker(env, task_queue="julep-agent-d", agents=agents_d):
        sid = f"agentd-{uuid.uuid4()}"
        res3 = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(controller="ctrl", session_id=sid, input=5, policy=ExecutionPolicy().to_json()),
            id=sid, task_queue="julep-agent-d",
        )
    assert res3["status"] == "denied", res3

    # Agent loops cannot open a human approval gate, so approval-required tools deny.
    agents_a = {
        "ctrl": {
            "config": {"maxRounds": 6, "budget": {"cost": 1000}},
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
    async with _worker(env, task_queue="julep-agent-a", agents=agents_a):
        sid = f"agenta-{uuid.uuid4()}"
        res4 = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(controller="ctrl", session_id=sid, input=5, policy=ExecutionPolicy().to_json()),
            id=sid, task_queue="julep-agent-a",
        )
    assert res4["status"] == "denied", res4
    assert res4["reason"] == "approval-required tool 'srv/double'; agent must ESCALATE"

    # maxCalls: the per-tool counter is carried through continue-as-new and
    # denies the second requested call before dispatching another effect.
    max_call_effects = {"count": 0}

    async def counted_mcp(server, tool, value, idempotency_key):  # noqa: ANN001
        max_call_effects["count"] += 1
        return await _mcp(server, tool, value, idempotency_key)

    async def max_calls_llm(reasoner, value):  # noqa: ANN001
        if reasoner.name == "max_ctrl":
            return {"tool": "srv/double", "input": value["input"]}
        return await _llm(reasoner, value)

    agents_m = {
        "max_ctrl": {
            "config": {
                "maxRounds": 6,
                "budget": {"cost": 1000},
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
        task_queue="julep-agent-m",
        agents=agents_m,
        llm=max_calls_llm,
        mcp_call=counted_mcp,
        extra_reasoners=(Reasoner(name="max_ctrl", model="test", system="max calls"),),
    ):
        sid = f"agentm-{uuid.uuid4()}"
        res5 = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(controller="max_ctrl", session_id=sid, input=5, policy=ExecutionPolicy().to_json()),
            id=sid,
            task_queue="julep-agent-m",
        )
    assert res5["status"] == "denied", res5
    assert res5["reason"] == "tool 'srv/double' exceeded maxCalls=1"
    assert [t["decision"] for t in res5["trace"]] == ["call"], res5
    assert max_call_effects["count"] == 1

    # Subflow grants: None is unconstrained, [] denies all, and a listed child
    # is allowed through the agent SUB path.
    async def subflow_llm(reasoner, value):  # noqa: ANN001
        if reasoner.name.startswith("sub_ctrl_"):
            if not value.get("trace"):
                return {"sub": "child", "input": value["input"]}
            return {"done": True, "output": value["input"]}
        return await _llm(reasoner, value)

    sub_agents = {
        "sub_ctrl_denied": {
            "config": {"maxRounds": 3, "budget": {"cost": 1000}},
            "grantedSubflows": ["other"],
        },
        "sub_ctrl_empty": {
            "config": {"maxRounds": 3, "budget": {"cost": 1000}},
            "grantedSubflows": [],
        },
        "sub_ctrl_allowed": {
            "config": {"maxRounds": 3, "budget": {"cost": 1000}},
            "grantedSubflows": ["child"],
        },
    }
    async with _worker(
        env,
        task_queue="julep-agent-sub",
        agents=sub_agents,
        llm=subflow_llm,
        extra_reasoners=(
            Reasoner(name="sub_ctrl_denied", model="test", system="sub denied"),
            Reasoner(name="sub_ctrl_empty", model="test", system="sub empty"),
            Reasoner(name="sub_ctrl_allowed", model="test", system="sub allowed"),
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
            task_queue="julep-agent-sub",
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
            task_queue="julep-agent-sub",
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
            task_queue="julep-agent-sub",
        )
    assert denied["status"] == "denied", denied
    assert denied["reason"] == "subflow 'child' is not granted"
    assert denied["trace"] == []
    assert empty["status"] == "denied", empty
    assert empty["reason"] == "subflow 'child' is not granted"
    assert allowed["status"] == "done", allowed
    assert allowed["output"] == 6, allowed
    assert [t["decision"] for t in allowed["trace"]] == ["sub"], allowed


async def _app_inline_grant_attenuation(env):
    async def app_llm(reasoner, value):  # noqa: ANN001
        if reasoner.name == "inline_missing_ctrl":
            if not value.get("trace"):
                return {"tool": "srv/echo", "input": value["input"]}
            return {"done": True, "output": value["input"]}
        if reasoner.name == "inline_allowed_ctrl":
            if not value.get("trace"):
                return {"tool": "srv/double", "input": value["input"]}
            return {"done": True, "output": value["input"]}
        return await _llm(reasoner, value)

    agents = {
        "inline_missing_ctrl": {
            "config": {"maxRounds": 3, "budget": {"cost": 1000}},
            "grantedTools": ["srv/double"],
        },
        "inline_allowed_ctrl": {
            "config": {"maxRounds": 3, "budget": {"cost": 1000}},
            "grantedTools": ["only/spec-should-not-be-used"],
        },
    }
    caps = CapabilityManifest.from_dict(
        {
            "tools": [{"name": "srv/double", "effect": "read", "idempotency": "native"}],
            "mcp_servers": {"srv": None},
        }
    )
    missing_tools = deploy(
        app("inline_missing_ctrl", budget=Budget(cost=1000)),
        _snapshot(),
        capabilities=caps,
    )
    allowed_inline = deploy(
        app("inline_allowed_ctrl", tools=["srv/double"], budget=Budget(cost=1000)),
        _snapshot(),
        capabilities=caps,
    )

    async with _worker(
        env,
        task_queue="julep-app-inline",
        agents=agents,
        llm=app_llm,
        extra_reasoners=(
            Reasoner(name="inline_missing_ctrl", model="test", system="inline missing"),
            Reasoner(name="inline_allowed_ctrl", model="test", system="inline allowed"),
        ),
    ):
        denied = await missing_tools.run(
            env.client,
            session_id=f"appinline-missing-{uuid.uuid4()}",
            input=5,
            task_queue="julep-app-inline",
        )
        allowed = await allowed_inline.run(
            env.client,
            session_id=f"appinline-allowed-{uuid.uuid4()}",
            input=5,
            task_queue="julep-app-inline",
        )

    assert denied["status"] == "denied", denied
    assert denied["reason"] == "tool 'srv/echo' is not granted"
    assert denied["trace"] == []
    assert allowed["status"] == "done", allowed
    assert allowed["output"] == 10, allowed
    assert [t["decision"] for t in allowed["trace"]] == ["call"], allowed


async def _app_max_calls_inherits_parent_counts(env):
    """An inline app cannot reset an already-consumed maxCalls budget: the
    parent env's call counts seed the child agent's state (parity with Sub)."""

    async def seed_llm(reasoner, value):  # noqa: ANN001
        if reasoner.name == "seeded_app_ctrl":
            return {"tool": "srv/double", "input": value["input"]}
        return await _llm(reasoner, value)

    agents = {
        "seeded_app_ctrl": {
            "config": {"maxRounds": 3, "budget": {"cost": 1000}},
            "grantedTools": ["srv/double"],
        },
    }
    parent = freeze(
        seq(
            call(mcp("srv", "double")),
            app("seeded_app_ctrl", tools=["srv/double"], budget=Budget(cost=1000)),
        ),
        _snapshot(),
    )

    async with _worker(
        env,
        task_queue="julep-app-seeded",
        agents=agents,
        llm=seed_llm,
        extra_reasoners=(Reasoner(name="seeded_app_ctrl", model="test", system="seeded app"),),
    ):
        res = await run_flow(
            env.client,
            parent.flow.to_json(),
            manifest_to_json(parent.manifest),
            session_id=f"appseed-{uuid.uuid4()}",
            input=5,
            task_queue="julep-app-seeded",
            max_call_limits={"srv/double": 1},
        )

    assert res["status"] == "denied", res
    assert res["reason"] == "tool 'srv/double' exceeded maxCalls=1", res
    assert res["trace"] == [], res


async def _strict_controller_contract(env):
    async def malformed_llm(reasoner, value):  # noqa: ANN001
        if reasoner.name in {"strict_malformed_ctrl", "permissive_malformed_ctrl"}:
            return "plain prose"
        return await _llm(reasoner, value)

    agents = {
        "strict_malformed_ctrl": {
            "config": {"maxRounds": 1, "budget": {"cost": 1000}},
        },
        "permissive_malformed_ctrl": {
            "config": {
                "maxRounds": 1,
                "budget": {"cost": 1000},
                "permissiveController": True,
            },
        },
    }
    async with _worker(
        env,
        task_queue="julep-strict-controller",
        agents=agents,
        llm=malformed_llm,
        extra_reasoners=(
            Reasoner(name="strict_malformed_ctrl", model="test", system="strict"),
            Reasoner(name="permissive_malformed_ctrl", model="test", system="permissive"),
        ),
    ):
        strict = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(
                controller="strict_malformed_ctrl",
                session_id=f"strictctrl-{uuid.uuid4()}",
                input=5,
                policy=ExecutionPolicy().to_json(),
            ),
            id=f"strictctrl-{uuid.uuid4()}",
            task_queue="julep-strict-controller",
        )
        permissive = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(
                controller="permissive_malformed_ctrl",
                session_id=f"permissivectrl-{uuid.uuid4()}",
                input=5,
                policy=ExecutionPolicy().to_json(),
            ),
            id=f"permissivectrl-{uuid.uuid4()}",
            task_queue="julep-strict-controller",
        )

    assert strict["status"] == "controller_error", strict
    assert "malformed controller reply" in strict["reason"]
    assert permissive["status"] == "done", permissive
    assert permissive["output"] == "plain prose", permissive


async def _sub_max_calls_inherits_parent_counts(env):
    effects = {"count": 0}

    async def counted_mcp(server, tool, value, idempotency_key):  # noqa: ANN001
        effects["count"] += 1
        return await _mcp(server, tool, value, idempotency_key)

    child = freeze(call(mcp("srv", "double")), _snapshot())
    child_registry = {
        "child-double": {
            "flowJson": child.flow.to_json(),
            "manifestJson": manifest_to_json(child.manifest),
        }
    }
    parent = freeze(seq(call(mcp("srv", "double")), sub("child-double", Contract.pipeline())), _snapshot())

    async with build_worker(
        env.client,
        WorkerContext(
            mcp_call=counted_mcp,
            llm=_llm,
            subflows=child_registry,
        ),
        task_queue="julep-sub-maxcalls",
    ):
        with pytest.raises(WorkflowFailureError) as raised:
            await run_flow(
                env.client,
                parent.flow.to_json(),
                manifest_to_json(parent.manifest),
                session_id=f"submax-denied-{uuid.uuid4()}",
                input=5,
                task_queue="julep-sub-maxcalls",
                max_call_limits={"srv/double": 1},
            )

        ok = await run_flow(
            env.client,
            parent.flow.to_json(),
            manifest_to_json(parent.manifest),
            session_id=f"submax-ok-{uuid.uuid4()}",
            input=5,
            task_queue="julep-sub-maxcalls",
            max_call_limits={"srv/double": 2},
        )

    cause = raised.value.__cause__
    while cause is not None and not (
        isinstance(cause, ApplicationError) and cause.type == "CapabilityDenied"
    ):
        cause = cause.__cause__

    assert isinstance(cause, ApplicationError)
    assert "exceeded maxCalls=1" in str(cause)
    assert ok == 20
    assert effects["count"] == 3


async def _agent_session_store(env):
    """The gated session-store seam is behaviour-preserving: routing AgentState
    through loadState/commitState at the continue-as-new boundary yields the same
    output as the default inline path, and commits >=1 revision to the store."""
    agents = {
        "ctrl": {
            "config": {
                "maxRounds": 6,
                "budget": {"cost": 1000},
                "continueAsNewAfter": 1,
            },
            "grantedTools": ["srv/double"],
        }
    }
    store = InMemorySessionStore()

    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="adder", model="test", system="add 10"))
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="ctrl", model="test", system="decide"))
    ctx = WorkerContext(
        mcp_call=_mcp,
        llm=_llm,
        subflows=_child_registry(),
        agents=agents,
        session_store=store,
    )
    configure(ctx)
    worker = Worker(
        env.client,
        task_queue="julep-agent-store",
        workflows=WORKFLOWS,
        activities=ACTIVITIES,
    )
    async with worker:
        sid = f"agent-store-{uuid.uuid4()}"
        res = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(
                controller="ctrl",
                session_id=sid,
                input=5,
                use_session_store=True,
                policy=ExecutionPolicy().to_json(),
            ),
            id=sid,
            task_queue="julep-agent-store",
        )

    # Same terminal result as the default inline path in _agent(env).
    assert res["status"] == "done", res
    assert res["output"] == 11, f"session-store agent expected 11, got {res['output']}"
    assert [t["decision"] for t in res["trace"]] == ["call", "sub"], res

    # The store actually received committed revisions (cursor path exercised).
    committed = sum(len(revs) for revs in store._revisions.values())
    assert committed >= 1, f"expected >=1 committed revision, got {committed}"


async def _agent_session_store_fencing(env):
    """Design invariant 1: when use_session_store=True the session_id must equal
    the Temporal workflow id (Temporal's one-running-execution-per-workflow-id is
    the store's only mutual-exclusion mechanism). A mismatched workflow id fails
    fast with a non-retryable ValidationError, before any LLM/reasoner effect."""
    agents = {
        "ctrl": {
            "config": {
                "maxRounds": 6,
                "budget": {"cost": 1000},
                "continueAsNewAfter": 1,
            },
            "grantedTools": ["srv/double"],
        }
    }
    store = InMemorySessionStore()
    llm_calls = {"count": 0}

    async def counting_llm(reasoner, value):  # noqa: ANN001
        llm_calls["count"] += 1
        return await _llm(reasoner, value)

    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="adder", model="test", system="add 10"))
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="ctrl", model="test", system="decide"))
    ctx = WorkerContext(
        mcp_call=_mcp,
        llm=counting_llm,
        subflows=_child_registry(),
        agents=agents,
        session_store=store,
    )
    configure(ctx)
    worker = Worker(
        env.client,
        task_queue="julep-agent-store-fencing",
        workflows=WORKFLOWS,
        activities=ACTIVITIES,
    )
    async with worker:
        sid = f"fenced-{uuid.uuid4()}"
        with pytest.raises(WorkflowFailureError) as raised:
            await env.client.execute_workflow(
                AgentWorkflow.run,
                AgentInput(
                    controller="ctrl",
                    session_id=sid,
                    input=5,
                    use_session_store=True,
                    policy=ExecutionPolicy().to_json(),
                ),
                id=f"other-{uuid.uuid4()}",
                task_queue="julep-agent-store-fencing",
            )

    cause = raised.value.__cause__
    while cause is not None and not (
        isinstance(cause, ApplicationError) and cause.type == "ValidationError"
    ):
        cause = cause.__cause__

    assert isinstance(cause, ApplicationError)
    assert cause.type == "ValidationError"
    assert "fencing" in str(cause)
    # The fence fires before any effect: the reasoner/LLM was never invoked.
    assert llm_calls["count"] == 0, f"expected 0 LLM calls, got {llm_calls['count']}"


async def _agent_trace_fidelity(env):
    """Context fidelity (off by default): with policy.trace_content_refs=True the
    CALL/SUB observations are offloaded through putBlob and stamped onto each
    TraceEntry as outputRef. The terminal output is unchanged from the default
    inline path, and the refs resolve through the blob store back to the recorded
    outputs. A default run records no outputRef (regression guard)."""
    agents = {
        "ctrl": {
            "config": {"maxRounds": 6, "budget": {"cost": 1000}},
            "grantedTools": ["srv/double"],
        }
    }
    blob_store = InMemoryBlobStore()

    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="adder", model="test", system="add 10"))
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="ctrl", model="test", system="decide"))
    ctx = WorkerContext(
        mcp_call=_mcp,
        llm=_llm,
        subflows=_child_registry(),
        agents=agents,
        blob_store=blob_store,
    )
    configure(ctx)
    worker = Worker(
        env.client,
        task_queue="julep-agent-fidelity",
        workflows=WORKFLOWS,
        activities=ACTIVITIES,
    )
    async with worker:
        # Fidelity ON: trace entries carry resolvable outputRefs.
        sid = f"agent-fidelity-{uuid.uuid4()}"
        res = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(
                controller="ctrl",
                session_id=sid,
                input=5,
                policy=ExecutionPolicy(trace_content_refs=True).to_json(),
            ),
            id=sid,
            task_queue="julep-agent-fidelity",
        )

        # Fidelity OFF (default): identical run, no outputRef recorded.
        sid_off = f"agent-fidelity-off-{uuid.uuid4()}"
        res_off = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(
                controller="ctrl",
                session_id=sid_off,
                input=5,
                policy=ExecutionPolicy().to_json(),
            ),
            id=sid_off,
            task_queue="julep-agent-fidelity",
        )

    # Same terminal result as the default inline path in _agent(env).
    assert res["status"] == "done", res
    assert res["output"] == 11, f"fidelity agent expected 11, got {res['output']}"
    assert [t["decision"] for t in res["trace"]] == ["call", "sub"], res
    assert res_off["status"] == "done", res_off
    assert res_off["output"] == 11, res_off

    # Fidelity ON: each entry carries an outputRef that resolves to its output.
    call_entry, sub_entry = res["trace"]
    assert call_entry["decision"] == "call"
    assert sub_entry["decision"] == "sub"
    call_ref = call_entry.get("outputRef")
    sub_ref = sub_entry.get("outputRef")
    assert call_ref is not None, f"call entry missing outputRef: {call_entry}"
    assert sub_ref is not None, f"sub entry missing outputRef: {sub_entry}"

    # The refs are tenant-scoped to the session and resolve to the outputs:
    # input 5 via srv/double is 10; the child sub then srv/inc gives 11.
    call_out = json.loads(await blob_store.get(sid, call_ref))
    sub_out = json.loads(await blob_store.get(sid, sub_ref))
    assert call_out == 10, f"call outputRef resolved to {call_out}, expected 10"
    assert sub_out == 11, f"sub outputRef resolved to {sub_out}, expected 11"

    # Fidelity OFF: regression guard — no outputRef stamped on any entry.
    assert all("outputRef" not in t for t in res_off["trace"]), res_off


async def _agent_require_tool_call_reasks_then_calls(env):
    agents = {
        "require_ctrl": {
            "config": {
                "requireToolCall": True,
                "maxRounds": 6,
                "budget": {"cost": 1000},
            },
            "grantedTools": ["srv/double"],
        }
    }
    calls = {"count": 0}

    async def scripted(reasoner, value):  # noqa: ANN001
        if reasoner.name != "require_ctrl":
            return await _llm(reasoner, value)
        calls["count"] += 1
        if calls["count"] == 1:
            return {"output": "premature text"}
        if calls["count"] == 2:
            assert value["input"] == {
                "error": REQUIRE_TOOL_CALL_REASK_MESSAGE,
                "reply": "premature text",
            }
            assert any(
                entry["decision"] == "reask"
                and entry["error"] == REQUIRE_TOOL_CALL_REASK_MESSAGE
                for entry in value["trace"]
            )
            return {"tool": "srv/double", "input": 5}
        return {"done": True, "output": value["input"]}

    async with _worker(
        env,
        task_queue="julep-agent-require-tool-call",
        agents=agents,
        llm=scripted,
        extra_reasoners=(Reasoner(name="require_ctrl", model="test", system="decide"),),
    ):
        sid = f"require-tool-call-{uuid.uuid4()}"
        res = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(
                controller="require_ctrl",
                session_id=sid,
                input={"task": "go"},
                policy=ExecutionPolicy().to_json(),
            ),
            id=sid,
            task_queue="julep-agent-require-tool-call",
        )

    assert res["status"] == "done", res
    assert res["output"] == 10, res
    reasks = [entry for entry in res["trace"] if entry["decision"] == "reask"]
    assert reasks == [
        {
            "decision": "reask",
            "cost": 0.0,
            "error": REQUIRE_TOOL_CALL_REASK_MESSAGE,
        }
    ]
    assert len(res["trace"]) == 2, res
    call_entry = res["trace"][1]
    assert call_entry["decision"] == "call"
    assert call_entry["ref"] == "srv/double"
    assert "error" not in call_entry


async def _agent_require_tool_call_halts(env):
    agents = {
        "require_ctrl2": {
            "config": {
                "requireToolCall": True,
                "maxRounds": 6,
                "budget": {"cost": 1000},
            },
            "grantedTools": ["srv/double"],
        }
    }

    async def scripted(reasoner, value):  # noqa: ANN001
        if reasoner.name == "require_ctrl2":
            return {"output": "text"}
        return await _llm(reasoner, value)

    async with _worker(
        env,
        task_queue="julep-agent-require-tool-call-halt",
        agents=agents,
        llm=scripted,
        extra_reasoners=(Reasoner(name="require_ctrl2", model="test", system="decide"),),
    ):
        sid = f"require-tool-call-halt-{uuid.uuid4()}"
        res = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(
                controller="require_ctrl2",
                session_id=sid,
                input={"task": "go"},
                policy=ExecutionPolicy().to_json(),
            ),
            id=sid,
            task_queue="julep-agent-require-tool-call-halt",
        )

    assert res["status"] == "controller_error", res
    assert res["reason"] == REQUIRE_TOOL_CALL_NEVER_CALLED_REASON
    reasks = [entry for entry in res["trace"] if entry["decision"] == "reask"]
    assert len(reasks) == 2, res
    assert all(entry["error"] == REQUIRE_TOOL_CALL_REASK_MESSAGE for entry in reasks)


async def _agent_tool_error_persisted_for_transcript(env):
    agents = {
        "err_ctrl": {
            "config": {"maxRounds": 4, "budget": {"cost": 1000}},
            "grantedTools": ["srv/fail"],
        }
    }
    blob_store = InMemoryBlobStore()
    calls = {"count": 0}

    async def scripted(reasoner, value):  # noqa: ANN001
        if reasoner.name != "err_ctrl":
            return await _llm(reasoner, value)
        calls["count"] += 1
        if calls["count"] == 1:
            return {"tool": "srv/fail", "input": 5}
        return {"done": True, "output": value["input"]}

    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="err_ctrl", model="test", system="decide"))
    ctx = WorkerContext(
        mcp_call=_mcp,
        llm=scripted,
        subflows=_child_registry(),
        agents=agents,
        blob_store=blob_store,
    )
    configure(ctx)
    worker = Worker(
        env.client,
        task_queue="julep-agent-tool-error-blob",
        workflows=WORKFLOWS,
        activities=ACTIVITIES,
    )
    async with worker:
        sid = f"agent-tool-error-blob-{uuid.uuid4()}"
        res = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(
                controller="err_ctrl",
                session_id=sid,
                input={"task": "go"},
                policy=ExecutionPolicy(
                    trace_content_refs=True,
                    idempotent_max_attempts=1,
                ).to_json(),
            ),
            id=sid,
            task_queue="julep-agent-tool-error-blob",
        )

    assert res["status"] == "done", res
    calls_trace = [entry for entry in res["trace"] if entry["decision"] == "call"]
    assert len(calls_trace) == 1, res
    call_entry = calls_trace[0]
    assert call_entry["ref"] == "srv/fail"
    assert call_entry.get("error")
    output_ref = call_entry.get("outputRef")
    assert output_ref, f"call entry missing outputRef: {call_entry}"

    resolved = json.loads(await blob_store.get(sid, output_ref))
    assert resolved["tool"] == "srv/fail"
    assert resolved["error"]


async def _pure_drift_fails_before_effect(env):
    effects = {"count": 0}

    async def mcp_counter(server, tool, value, idempotency_key):  # noqa: ANN001
        effects["count"] += 1
        return await _mcp(server, tool, value, idempotency_key)

    purity._REGISTRY["e2e.drift"] = PureEntry("e2e.drift", _drift_pure, "pure:pinned")
    deployment = deploy(seq(arr("e2e.drift"), call(mcp("srv", "inc"))), _snapshot())
    purity._REGISTRY["e2e.drift"] = PureEntry("e2e.drift", _drift_pure, "pure:changed")

    ctx = WorkerContext(mcp_call=mcp_counter, llm=_llm, subflows=_child_registry())
    async with build_worker(env.client, ctx, task_queue="julep-pure-drift"):
        with pytest.raises(WorkflowFailureError) as raised:
            await deployment.run(
                env.client,
                session_id=f"pure-drift-{uuid.uuid4()}",
                input=5,
                task_queue="julep-pure-drift",
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


async def _agent_native_tools_call_many(env):
    tool_defs = [
        {
            "type": "function",
            "function": {
                "name": "srv/double",
                "description": "",
                "parameters": {"type": "number"},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "srv/inc",
                "description": "",
                "parameters": {"type": "number"},
            },
        },
    ]
    agents = {
        "native_multi_ctrl": {
            "config": {
                "nativeTools": True,
                "maxRounds": 4,
                "budget": {"cost": 1000},
            },
            "grantedTools": ["srv/double", "srv/inc"],
            "grantedContracts": {
                "srv/double": {"effect": "read", "idempotency": "native"},
                "srv/inc": {"effect": "read", "idempotency": "native"},
            },
            "toolDefs": tool_defs,
        }
    }
    seen_values = []
    effects = []

    async def native_llm(reasoner, value, principal, transcript, dispatch, *, tools=None):  # noqa: ANN001
        del principal, transcript, dispatch
        assert reasoner.name == "native_multi_ctrl"
        assert tools == tool_defs
        seen_values.append(value)
        if len(seen_values) == 1:
            return {
                "tool_calls": [
                    {"id": "a", "tool": "srv/double", "input": 2},
                    {"id": "b", "tool": "srv/inc", "input": 4},
                ]
            }
        assert value["input"] == [
            {"id": "a", "tool": "srv/double", "output": 4},
            {"id": "b", "tool": "srv/inc", "output": 5},
        ]
        return {"done": True, "output": value["input"]}

    async def counted_mcp(server, tool, value, idempotency_key):  # noqa: ANN001
        effects.append((server, tool, value, idempotency_key))
        return await _mcp(server, tool, value, idempotency_key)

    async with _worker(
        env,
        task_queue="julep-agent-native-tools",
        agents=agents,
        llm=native_llm,
        mcp_call=counted_mcp,
        extra_reasoners=(Reasoner(name="native_multi_ctrl", model="test", system="native"),),
    ):
        sid = f"native-tools-{uuid.uuid4()}"
        res = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(
                controller="native_multi_ctrl",
                session_id=sid,
                input={"task": "go"},
                policy=ExecutionPolicy().to_json(),
            ),
            id=sid,
            task_queue="julep-agent-native-tools",
        )

    assert res["status"] == "done", res
    assert res["rounds"] == 1, res
    assert res["output"] == [
        {"id": "a", "tool": "srv/double", "output": 4},
        {"id": "b", "tool": "srv/inc", "output": 5},
    ]
    assert [(t["decision"], t["ref"], t["callId"]) for t in res["trace"]] == [
        ("call", "srv/double", "a"),
        ("call", "srv/inc", "b"),
    ]
    # Both calls are READ-effect and run concurrently, so activity arrival
    # order is nondeterministic; assert the sibling cids, not their order.
    assert sorted(item[3] for item in effects) == [
        f"{sid}-call-0-0",
        f"{sid}-call-0-1",
    ]
    assert seen_values[1]["input"] == res["output"]


async def _agent_native_tools_llm_result_meta_unwrap(env):
    tool_defs = [
        {
            "type": "function",
            "function": {
                "name": "srv/double",
                "description": "",
                "parameters": {"type": "number"},
            },
        },
    ]
    agents = {
        "native_llm_result_ctrl": {
            "config": {
                "nativeTools": True,
                "maxRounds": 4,
                "budget": {"cost": 1000},
            },
            "grantedTools": ["srv/double"],
            "grantedContracts": {
                "srv/double": {"effect": "read", "idempotency": "native"},
            },
            "toolDefs": tool_defs,
        }
    }
    seen_values = []
    effects = []

    def meta() -> LlmCallMeta:
        return LlmCallMeta(served_model="gpt-test", provider="openai")

    async def native_llm(reasoner, value, principal, transcript, dispatch, *, tools=None):  # noqa: ANN001
        del principal, transcript, dispatch
        assert reasoner.name == "native_llm_result_ctrl"
        assert tools == tool_defs
        seen_values.append(value)
        if len(seen_values) == 1:
            return LlmResult(
                reply={
                    "tool_calls": [
                        {"id": "a", "tool": "srv/double", "input": 2},
                    ],
                },
                meta=meta(),
            )
        assert value["input"] == [{"id": "a", "tool": "srv/double", "output": 4}]
        return LlmResult(reply={"done": True, "output": "done"}, meta=meta())

    async def counted_mcp(server, tool, value, idempotency_key):  # noqa: ANN001
        effects.append((server, tool, value, idempotency_key))
        return await _mcp(server, tool, value, idempotency_key)

    async with _worker(
        env,
        task_queue="julep-agent-native-tools-llm-result",
        agents=agents,
        llm=native_llm,
        mcp_call=counted_mcp,
        extra_reasoners=(Reasoner(name="native_llm_result_ctrl", model="test", system="native"),),
    ):
        sid = f"native-tools-llm-result-{uuid.uuid4()}"
        res = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(
                controller="native_llm_result_ctrl",
                session_id=sid,
                input={"task": "go"},
                policy=ExecutionPolicy().to_json(),
            ),
            id=sid,
            task_queue="julep-agent-native-tools-llm-result",
        )

    assert res["status"] == "done", res
    assert res["rounds"] == 1, res
    assert res["output"] == "done"
    assert [(t["decision"], t["ref"], t["callId"]) for t in res["trace"]] == [
        ("call", "srv/double", "a"),
    ]
    assert effects == [("srv", "double", 2, f"{sid}-call-0-0")]


async def _agent_call_many_tool_error_folds_to_observation(env):
    tool_defs = [
        {
            "type": "function",
            "function": {
                "name": "srv/double",
                "description": "",
                "parameters": {"type": "number"},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "srv/fail",
                "description": "",
                "parameters": {"type": "number"},
            },
        },
    ]
    agents = {
        "native_error_ctrl": {
            "config": {
                "nativeTools": True,
                "maxRounds": 4,
                "budget": {"cost": 1000},
            },
            "grantedTools": ["srv/double", "srv/fail"],
            "grantedContracts": {
                "srv/double": {"effect": "read", "idempotency": "native"},
                "srv/fail": {"effect": "read", "idempotency": "native"},
            },
            "toolDefs": tool_defs,
        }
    }
    seen_values = []

    async def native_llm(reasoner, value, principal, transcript, dispatch, *, tools=None):  # noqa: ANN001
        del principal, transcript, dispatch
        assert reasoner.name == "native_error_ctrl"
        assert tools == tool_defs
        seen_values.append(value)
        if len(seen_values) == 1:
            return {
                "tool_calls": [
                    {"id": "ok", "tool": "srv/double", "input": 3},
                    {"id": "bad", "tool": "srv/fail", "input": 1},
                ]
            }
        observations = value["input"]
        assert observations[0] == {"id": "ok", "tool": "srv/double", "output": 6}
        failed = observations[1]
        assert failed["id"] == "bad"
        assert failed["tool"] == "srv/fail"
        failed_output = failed["output"]
        assert isinstance(failed_output, dict)
        assert failed_output["tool"] == "srv/fail"
        assert failed_output["error"]
        return {"done": True, "output": observations}

    async with _worker(
        env,
        task_queue="julep-agent-call-many-tool-error",
        agents=agents,
        llm=native_llm,
        extra_reasoners=(Reasoner(name="native_error_ctrl", model="test", system="native"),),
    ):
        sid = f"native-tools-error-{uuid.uuid4()}"
        res = await env.client.execute_workflow(
            AgentWorkflow.run,
            AgentInput(
                controller="native_error_ctrl",
                session_id=sid,
                input={"task": "go"},
                policy=ExecutionPolicy().to_json(),
            ),
            id=sid,
            task_queue="julep-agent-call-many-tool-error",
        )

    assert res["status"] == "done", res
    assert res["output"][0] == {"id": "ok", "tool": "srv/double", "output": 6}
    failed = res["output"][1]
    assert failed["id"] == "bad"
    assert failed["tool"] == "srv/fail"
    failed_output = failed["output"]
    assert isinstance(failed_output, dict)
    assert failed_output["tool"] == "srv/fail"
    assert failed_output["error"]

    calls = [t for t in res["trace"] if t["decision"] == "call"]
    assert [(t["ref"], t["callId"]) for t in calls] == [
        ("srv/double", "ok"),
        ("srv/fail", "bad"),
    ]
    assert "error" not in calls[0]
    assert calls[1].get("error")
    assert seen_values[1]["input"] == res["output"]


async def _agent_native_tools_without_tool_defs_fails(env):
    async with _worker(
        env,
        task_queue="julep-agent-native-tools-missing",
        extra_reasoners=(
            Reasoner(name="native_missing_defs_ctrl", model="test", system="native"),
        ),
    ):
        sid = f"native-tools-missing-{uuid.uuid4()}"
        with pytest.raises(WorkflowFailureError) as raised:
            await env.client.execute_workflow(
                AgentWorkflow.run,
                AgentInput(
                    controller="native_missing_defs_ctrl",
                    session_id=sid,
                    input={"task": "go"},
                    config={
                        "nativeTools": True,
                        "maxRounds": 1,
                        "budget": {"cost": 1000},
                    },
                    granted_tools=["srv/double"],
                    policy=ExecutionPolicy().to_json(),
                    resolve_spec=False,
                ),
                id=sid,
                task_queue="julep-agent-native-tools-missing",
            )

    cause = raised.value.__cause__
    while cause is not None and not (
        isinstance(cause, ApplicationError) and cause.type == "ValidationError"
    ):
        cause = cause.__cause__

    assert isinstance(cause, ApplicationError)
    assert "native_tools on a durable backend needs provider tool definitions" in str(cause)


async def _run_all():
    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _pipeline_and_reasoner(env)
        await _queue_lanes_do_not_break_subflow_inheritance(env)
        await _agent_sub_routes_to_mapped_lane(env)
        await _principal_threading(env)
        await _race(env)
        await _human_gate(env)
        await _human_gate_timeout(env)
        await _generic_worker_agent_loop(env)
        await _agent(env)
        await _app_inline_grant_attenuation(env)
        await _app_max_calls_inherits_parent_counts(env)
        await _strict_controller_contract(env)
        await _sub_max_calls_inherits_parent_counts(env)
        await _agent_session_store(env)
        await _agent_session_store_fencing(env)
        await _agent_trace_fidelity(env)
        await _agent_require_tool_call_reasks_then_calls(env)
        await _agent_require_tool_call_halts(env)
        await _agent_tool_error_persisted_for_transcript(env)
        await _pure_drift_fails_before_effect(env)
        await _agent_native_tools_call_many(env)
        await _agent_native_tools_llm_result_meta_unwrap(env)
        await _agent_call_many_tool_error_folds_to_observation(env)
        await _agent_native_tools_without_tool_defs_fails(env)


def test_temporal_end_to_end():
    """Run all E2E flows in one time-skipping environment."""
    asyncio.run(asyncio.wait_for(_run_all(), timeout=180))
