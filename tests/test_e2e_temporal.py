"""End-to-end tests against Temporal's time-skipping test server.

Skipped entirely when ``temporalio`` is not installed. All four verified flows
run inside a single :class:`WorkflowEnvironment` (one server start, amortized)
driven by a synchronous wrapper, so the module needs no pytest-asyncio config.

Effect handlers are injected in-process callables (an MCP caller and an LLM), so
no HTTP hand server is required; native hands would need one.
"""

from __future__ import annotations

import asyncio
import json
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
        app,
        Budget,
        CapabilityManifest,
        Contract,
        sub,
    )
    from composable_agents.derived import race, human_gate
    from composable_agents.freeze import (
        McpSnapshot, McpServerSnapshot, McpToolSpec,
    )
    from composable_agents.contracts import McpAnnotations
    from composable_agents.execution.harness import (
        run_flow, start_flow, AgentWorkflow, AgentInput, ExecutionPolicy,
    )
    from composable_agents.execution.worker import build_worker, WORKFLOWS, ACTIVITIES
    from composable_agents.execution.activities import (
        WorkerContext, configure,
    )
    from composable_agents.execution.session_store import InMemorySessionStore
    from composable_agents.execution.blobstore import InMemoryBlobStore
    from temporalio.worker import Worker
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


async def _principal_threading(env):
    """Dispatch-supplied principal reaches a new-style MCP caller end-to-end."""
    seen = {}

    async def principal_mcp(server, tool, value, idempotency_key, principal):
        seen["principal"] = principal
        return await _mcp(server, tool, value, idempotency_key)

    fr = freeze(call(mcp("srv", "double")), _snapshot())
    async with _worker(env, task_queue="ca-principal", mcp_call=principal_mcp):
        out = await run_flow(
            env.client, fr.flow.to_json(), manifest_to_json(fr.manifest),
            session_id=f"principal-{uuid.uuid4()}", input=3, task_queue="ca-principal",
            principal={"storeId": 413, "tokenRef": "cred_abc"},
        )
    assert out == 6, f"principal flow expected 6, got {out}"
    assert seen["principal"] == {"storeId": 413, "tokenRef": "cred_abc"}, seen


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


async def _human_gate_timeout(env):
    fr = freeze(human_gate(timeout_s=1), _snapshot())
    async with _worker(env, task_queue="ca-gate-timeout"):
        out = await run_flow(
            env.client,
            fr.flow.to_json(),
            manifest_to_json(fr.manifest),
            session_id=f"gate-timeout-{uuid.uuid4()}",
            input={"q": "timeout"},
            task_queue="ca-gate-timeout",
        )
    assert out == {
        "approved": False,
        "reason": "timeout",
        "input": {"q": "timeout"},
    }, f"gate timeout lost original input: {out}"


async def _agent(env):
    agents = {"ctrl": {"config": {"maxRounds": 6, "budget": {"cost": 1000}}, "grantedTools": ["srv/double"]}}
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
            "config": {"maxRounds": 6, "budget": {"cost": 0.5}},
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
    assert res2["cost"] == 0, res2
    assert res2["trace"] == [], res2
    assert budget_brain_calls["count"] == 0

    # Capability deny: the requested tool is not granted.
    agents_d = {"ctrl": {"config": {"maxRounds": 6, "budget": {"cost": 1000}}, "grantedTools": ["only/other"]}}
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


async def _app_inline_grant_attenuation(env):
    async def app_llm(brain, value):  # noqa: ANN001
        if brain.name == "inline_missing_ctrl":
            if not value.get("trace"):
                return {"tool": "srv/echo", "input": value["input"]}
            return {"done": True, "output": value["input"]}
        if brain.name == "inline_allowed_ctrl":
            if not value.get("trace"):
                return {"tool": "srv/double", "input": value["input"]}
            return {"done": True, "output": value["input"]}
        return await _llm(brain, value)

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
        task_queue="ca-app-inline",
        agents=agents,
        llm=app_llm,
        extra_brains=(
            Brain(name="inline_missing_ctrl", model="test", system="inline missing"),
            Brain(name="inline_allowed_ctrl", model="test", system="inline allowed"),
        ),
    ):
        denied = await missing_tools.run(
            env.client,
            session_id=f"appinline-missing-{uuid.uuid4()}",
            input=5,
            task_queue="ca-app-inline",
        )
        allowed = await allowed_inline.run(
            env.client,
            session_id=f"appinline-allowed-{uuid.uuid4()}",
            input=5,
            task_queue="ca-app-inline",
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

    async def seed_llm(brain, value):  # noqa: ANN001
        if brain.name == "seeded_app_ctrl":
            return {"tool": "srv/double", "input": value["input"]}
        return await _llm(brain, value)

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
        task_queue="ca-app-seeded",
        agents=agents,
        llm=seed_llm,
        extra_brains=(Brain(name="seeded_app_ctrl", model="test", system="seeded app"),),
    ):
        res = await run_flow(
            env.client,
            parent.flow.to_json(),
            manifest_to_json(parent.manifest),
            session_id=f"appseed-{uuid.uuid4()}",
            input=5,
            task_queue="ca-app-seeded",
            max_call_limits={"srv/double": 1},
        )

    assert res["status"] == "denied", res
    assert res["reason"] == "tool 'srv/double' exceeded maxCalls=1", res
    assert res["trace"] == [], res


async def _strict_controller_contract(env):
    async def malformed_llm(brain, value):  # noqa: ANN001
        if brain.name in {"strict_malformed_ctrl", "permissive_malformed_ctrl"}:
            return "plain prose"
        return await _llm(brain, value)

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
        task_queue="ca-strict-controller",
        agents=agents,
        llm=malformed_llm,
        extra_brains=(
            Brain(name="strict_malformed_ctrl", model="test", system="strict"),
            Brain(name="permissive_malformed_ctrl", model="test", system="permissive"),
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
            task_queue="ca-strict-controller",
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
            task_queue="ca-strict-controller",
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
        task_queue="ca-sub-maxcalls",
    ):
        with pytest.raises(WorkflowFailureError) as raised:
            await run_flow(
                env.client,
                parent.flow.to_json(),
                manifest_to_json(parent.manifest),
                session_id=f"submax-denied-{uuid.uuid4()}",
                input=5,
                task_queue="ca-sub-maxcalls",
                max_call_limits={"srv/double": 1},
            )

        ok = await run_flow(
            env.client,
            parent.flow.to_json(),
            manifest_to_json(parent.manifest),
            session_id=f"submax-ok-{uuid.uuid4()}",
            input=5,
            task_queue="ca-sub-maxcalls",
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

    register_brain(Brain(name="adder", model="test", system="add 10"))
    register_brain(Brain(name="ctrl", model="test", system="decide"))
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
        task_queue="ca-agent-store",
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
            task_queue="ca-agent-store",
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
    fast with a non-retryable ValidationError, before any LLM/brain effect."""
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

    async def counting_llm(brain, value):  # noqa: ANN001
        llm_calls["count"] += 1
        return await _llm(brain, value)

    register_brain(Brain(name="adder", model="test", system="add 10"))
    register_brain(Brain(name="ctrl", model="test", system="decide"))
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
        task_queue="ca-agent-store-fencing",
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
                task_queue="ca-agent-store-fencing",
            )

    cause = raised.value.__cause__
    while cause is not None and not (
        isinstance(cause, ApplicationError) and cause.type == "ValidationError"
    ):
        cause = cause.__cause__

    assert isinstance(cause, ApplicationError)
    assert cause.type == "ValidationError"
    assert "fencing" in str(cause)
    # The fence fires before any effect: the brain/LLM was never invoked.
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

    register_brain(Brain(name="adder", model="test", system="add 10"))
    register_brain(Brain(name="ctrl", model="test", system="decide"))
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
        task_queue="ca-agent-fidelity",
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
            task_queue="ca-agent-fidelity",
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
            task_queue="ca-agent-fidelity",
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
        await _principal_threading(env)
        await _race(env)
        await _human_gate(env)
        await _human_gate_timeout(env)
        await _agent(env)
        await _app_inline_grant_attenuation(env)
        await _app_max_calls_inherits_parent_counts(env)
        await _strict_controller_contract(env)
        await _sub_max_calls_inherits_parent_counts(env)
        await _agent_session_store(env)
        await _agent_session_store_fencing(env)
        await _agent_trace_fidelity(env)
        await _pure_drift_fails_before_effect(env)


def test_temporal_end_to_end():
    """Run all E2E flows in one time-skipping environment."""
    asyncio.run(asyncio.wait_for(_run_all(), timeout=180))
