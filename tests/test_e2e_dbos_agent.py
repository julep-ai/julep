"""End-to-end agent loops (``ca_agent``) on a real DBOS runtime.

Each test mirrors a Temporal ``_agent`` scenario from tests/test_e2e_temporal.py.
Needs ``DBOS_TEST_DATABASE_URL`` (see tests/test_dbos_api_spike.py). Reuses one
module-scoped event loop for the same executor reason as tests/test_e2e_dbos.py.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import Awaitable, Callable, Iterator
from typing import Any, TypeVar

import pytest

from composable_agents.execution import HAVE_DBOS

DB_URL = os.environ.get("DBOS_TEST_DATABASE_URL")
T = TypeVar("T")
pytestmark = pytest.mark.skipif(
    not HAVE_DBOS or not DB_URL,
    reason="dbos not installed or DBOS_TEST_DATABASE_URL not set",
)

if HAVE_DBOS and DB_URL:
    from dbos import DBOS, DBOSConfig

    from composable_agents import (
        Reasoner,
        Budget,
        app,
        call,
        freeze,
        manifest_to_json,
        mcp,
        register_reasoner,
        seq,
    )
    from composable_agents.contracts import McpAnnotations
    from composable_agents.derived import human_gate
    from composable_agents.execution.dbos_backend import (
        run_agent_dbos,
        run_flow_dbos,
        submit_human_dbos,
    )
    from composable_agents.execution.effects import WorkerContext, configure
    from composable_agents.freeze import McpServerSnapshot, McpSnapshot, McpToolSpec

    def _snapshot() -> McpSnapshot:
        ann = McpAnnotations(read_only_hint=True, idempotent_hint=True)
        return McpSnapshot(
            servers={
                "srv": McpServerSnapshot(
                    server="srv",
                    version="1",
                    tools={
                        t: McpToolSpec(input_schema={}, annotations=ann)
                        for t in ("double", "inc", "echo")
                    },
                )
            }
        )

    _EFFECTS = {"count": 0}
    _LLM_CALLS = {"dbos_budget_ctrl": 0}

    async def fake_mcp(server: str, tool: str, value: Any, key: str) -> Any:
        assert key
        _EFFECTS["count"] += 1
        if tool == "double":
            return value * 2
        if tool == "inc":
            return value + 1
        if tool == "echo":
            return value
        raise ValueError(tool)

    async def fake_llm(reasoner: Any, value: Any) -> Any:
        name = reasoner.name
        if name == "dbos_ctrl":
            n = len(value.get("trace", []))
            if n == 0:
                return {"tool": "srv/double", "input": value["input"]}
            if n == 1:
                return {"sub": "child"}
            return {"done": True, "output": value["input"]}
        if name == "dbos_budget_ctrl":
            _LLM_CALLS["dbos_budget_ctrl"] += 1
            raise RuntimeError("budget controller should not be invoked")
        if name in ("dbos_denied_ctrl", "dbos_approval_ctrl", "dbos_max_ctrl", "dbos_seed_ctrl"):
            return {"tool": "srv/double", "input": value["input"]}
        if name == "dbos_seg_ctrl":
            if len(value.get("trace", [])) < 5:
                return {"tool": "srv/double", "input": value["input"]}
            return {"done": True, "output": value["input"]}
        if name.startswith("dbos_sub_ctrl_"):
            if not value.get("trace"):
                return {"sub": "child", "input": value["input"]}
            return {"done": True, "output": value["input"]}
        if name == "dbos_gate_ctrl":
            if not value.get("trace"):
                return {"sub": "gated", "input": value["input"]}
            return {"done": True, "output": value["input"]}
        if name == "dbos_app_missing_ctrl":
            if not value.get("trace"):
                return {"tool": "srv/echo", "input": value["input"]}
            return {"done": True, "output": value["input"]}
        if name == "dbos_app_allowed_ctrl":
            if not value.get("trace"):
                return {"tool": "srv/double", "input": value["input"]}
            return {"done": True, "output": value["input"]}
        return value

    def _subflows() -> dict[str, dict[str, Any]]:
        child = freeze(call(mcp("srv", "inc")), _snapshot())
        gated = freeze(human_gate(timeout_s=30), _snapshot())
        return {
            "child": {
                "flowJson": child.flow.to_json(),
                "manifestJson": manifest_to_json(child.manifest),
            },
            "gated": {
                "flowJson": gated.flow.to_json(),
                "manifestJson": manifest_to_json(gated.manifest),
            },
        }

    _AGENTS = {
        "dbos_ctrl": {
            "config": {"maxRounds": 6, "budget": {"cost": 1000}},
            "grantedTools": ["srv/double"],
        },
        "dbos_budget_ctrl": {
            "config": {"maxRounds": 6, "budget": {"cost": 0.5}},
            "grantedTools": ["srv/double"],
        },
        "dbos_denied_ctrl": {
            "config": {"maxRounds": 6, "budget": {"cost": 1000}},
            "grantedTools": ["only/other"],
        },
        "dbos_approval_ctrl": {
            "config": {"maxRounds": 6, "budget": {"cost": 1000}},
            "grantedTools": ["srv/double"],
            "grantedContracts": {
                "srv/double": {
                    "effect": "read",
                    "idempotency": "native",
                    "approval": True,
                }
            },
        },
        "dbos_max_ctrl": {
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
        },
        "dbos_seg_ctrl": {
            "config": {
                "maxRounds": 10,
                "budget": {"cost": 1000},
                "continueAsNewAfter": 2,
            },
            "grantedTools": ["srv/double"],
        },
        "dbos_seed_ctrl": {
            "config": {"maxRounds": 3, "budget": {"cost": 1000}},
            "grantedTools": ["srv/double"],
        },
        "dbos_sub_ctrl_denied": {
            "config": {"maxRounds": 3, "budget": {"cost": 1000}},
            "grantedSubflows": ["other"],
        },
        "dbos_sub_ctrl_empty": {
            "config": {"maxRounds": 3, "budget": {"cost": 1000}},
            "grantedSubflows": [],
        },
        "dbos_sub_ctrl_allowed": {
            "config": {"maxRounds": 3, "budget": {"cost": 1000}},
            "grantedSubflows": ["child"],
        },
        "dbos_gate_ctrl": {
            "config": {"maxRounds": 3, "budget": {"cost": 1000}},
            "grantedSubflows": ["gated"],
        },
    }

    _CONTROLLERS = (
        "dbos_ctrl",
        "dbos_budget_ctrl",
        "dbos_denied_ctrl",
        "dbos_approval_ctrl",
        "dbos_max_ctrl",
        "dbos_seg_ctrl",
        "dbos_seed_ctrl",
        "dbos_sub_ctrl_denied",
        "dbos_sub_ctrl_empty",
        "dbos_sub_ctrl_allowed",
        "dbos_gate_ctrl",
        "dbos_app_missing_ctrl",
        "dbos_app_allowed_ctrl",
    )


@pytest.fixture(scope="module")
def run_async() -> Iterator[Callable[[Awaitable[T]], T]]:
    loop = asyncio.new_event_loop()

    def run(awaitable: Awaitable[T]) -> T:
        return loop.run_until_complete(awaitable)

    yield run
    loop.close()


@pytest.fixture(scope="module")
def dbos_runtime(run_async: Callable[[Awaitable[Any]], Any]) -> Iterator[None]:
    for name in _CONTROLLERS:
        register_reasoner(Reasoner(name=name, model="test", system=name))
    configure(
        WorkerContext(
            mcp_call=fake_mcp,
            llm=fake_llm,
            subflows=_subflows(),
            agents=_AGENTS,
        )
    )
    DBOS(
        config=DBOSConfig(
            name=f"ca-e2e-agent-{uuid.uuid4().hex[:8]}",
            system_database_url=DB_URL,
        )
    )
    DBOS.launch()
    yield
    DBOS.destroy()


def test_agent_done_call_then_sub(
    dbos_runtime: None, run_async: Callable[[Awaitable[dict[str, Any]]], dict[str, Any]]
) -> None:
    res = run_async(
        run_agent_dbos("dbos_ctrl", session_id=f"agent-{uuid.uuid4().hex[:8]}", input=5)
    )
    assert res["status"] == "done", res
    assert res["output"] == 11, res
    assert [t["decision"] for t in res["trace"]] == ["call", "sub"], res


def test_agent_over_budget_without_reasoner_call(
    dbos_runtime: None, run_async: Callable[[Awaitable[dict[str, Any]]], dict[str, Any]]
) -> None:
    res = run_async(
        run_agent_dbos("dbos_budget_ctrl", session_id=f"agentb-{uuid.uuid4().hex[:8]}", input=5)
    )
    assert res["status"] == "over_budget", res
    assert res["cost"] == 0, res
    assert res["trace"] == [], res
    assert _LLM_CALLS["dbos_budget_ctrl"] == 0


def test_agent_denies_ungranted_tool(
    dbos_runtime: None, run_async: Callable[[Awaitable[dict[str, Any]]], dict[str, Any]]
) -> None:
    res = run_async(
        run_agent_dbos("dbos_denied_ctrl", session_id=f"agentd-{uuid.uuid4().hex[:8]}", input=5)
    )
    assert res["status"] == "denied", res
    assert res["reason"] == "tool 'srv/double' is not granted", res


def test_agent_denies_approval_required_tool(
    dbos_runtime: None, run_async: Callable[[Awaitable[dict[str, Any]]], dict[str, Any]]
) -> None:
    res = run_async(
        run_agent_dbos("dbos_approval_ctrl", session_id=f"agenta-{uuid.uuid4().hex[:8]}", input=5)
    )
    assert res["status"] == "denied", res
    assert res["reason"] == "approval-required tool 'srv/double'; agent must ESCALATE"


def test_agent_max_calls_across_segments(
    dbos_runtime: None, run_async: Callable[[Awaitable[dict[str, Any]]], dict[str, Any]]
) -> None:
    _EFFECTS["count"] = 0
    sid = f"agentm-{uuid.uuid4().hex[:8]}"
    res = run_async(run_agent_dbos("dbos_max_ctrl", session_id=sid, input=5))
    assert res["status"] == "denied", res
    assert res["reason"] == "tool 'srv/double' exceeded maxCalls=1", res
    assert [t["decision"] for t in res["trace"]] == ["call"], res
    assert _EFFECTS["count"] == 1, _EFFECTS

    # continueAsNewAfter=1 chained a second segment with the derived id.
    async def seg1_status() -> Any:
        return await DBOS.get_workflow_status_async(f"{sid}-seg1")

    assert run_async(seg1_status()) is not None


def test_agent_segment_local_continue_as_new_cadence(
    dbos_runtime: None, run_async: Callable[[Awaitable[dict[str, Any]]], dict[str, Any]]
) -> None:
    # 5 tool rounds then finish, with continueAsNewAfter=2: truncation fires
    # every 2 segment-local rounds, so the chain is base (rounds 1-2),
    # seg1 (rounds 3-4), seg2 (round 5 + finish). Under the old cumulative
    # check, every segment after the first ran exactly one round, so a seg3
    # (and seg4) would exist.
    sid = f"agentseg-{uuid.uuid4().hex[:8]}"
    res = run_async(run_agent_dbos("dbos_seg_ctrl", session_id=sid, input=1))
    assert res["status"] == "done", res
    assert res["output"] == 32, res
    assert res["rounds"] == 5, res
    assert [t["decision"] for t in res["trace"]] == ["call"] * 5, res

    async def segment_statuses() -> list[Any]:
        return [
            await DBOS.get_workflow_status_async(f"{sid}-seg{i}") for i in (1, 2, 3)
        ]

    seg1, seg2, seg3 = run_async(segment_statuses())
    assert seg1 is not None, f"expected {sid}-seg1 (rounds 3-4)"
    assert seg2 is not None, f"expected {sid}-seg2 (round 5 + finish)"
    assert seg3 is None, f"{sid}-seg3 must not exist: cadence is per segment"


def test_agent_subflow_grants(
    dbos_runtime: None, run_async: Callable[[Awaitable[dict[str, Any]]], dict[str, Any]]
) -> None:
    denied = run_async(
        run_agent_dbos(
            "dbos_sub_ctrl_denied", session_id=f"agentsubd-{uuid.uuid4().hex[:8]}", input=5
        )
    )
    empty = run_async(
        run_agent_dbos(
            "dbos_sub_ctrl_empty", session_id=f"agentsube-{uuid.uuid4().hex[:8]}", input=5
        )
    )
    allowed = run_async(
        run_agent_dbos(
            "dbos_sub_ctrl_allowed", session_id=f"agentsuba-{uuid.uuid4().hex[:8]}", input=5
        )
    )
    assert denied["status"] == "denied", denied
    assert denied["reason"] == "subflow 'child' is not granted"
    assert denied["trace"] == []
    assert empty["status"] == "denied", empty
    assert empty["reason"] == "subflow 'child' is not granted"
    assert allowed["status"] == "done", allowed
    assert allowed["output"] == 6, allowed
    assert [t["decision"] for t in allowed["trace"]] == ["sub"], allowed


def test_app_node_inside_flow(
    dbos_runtime: None, run_async: Callable[[Awaitable[dict[str, Any]]], dict[str, Any]]
) -> None:
    # Inline app grants attenuate: the node's tools list is the allow-list.
    missing = freeze(
        app("dbos_app_missing_ctrl", tools=["srv/double"], budget=Budget(cost=1000)),
        _snapshot(),
    )
    allowed = freeze(
        app("dbos_app_allowed_ctrl", tools=["srv/double"], budget=Budget(cost=1000)),
        _snapshot(),
    )

    denied = run_async(
        run_flow_dbos(
            missing.flow.to_json(),
            manifest_to_json(missing.manifest),
            session_id=f"appflow-missing-{uuid.uuid4().hex[:8]}",
            input=5,
        )
    )
    done = run_async(
        run_flow_dbos(
            allowed.flow.to_json(),
            manifest_to_json(allowed.manifest),
            session_id=f"appflow-allowed-{uuid.uuid4().hex[:8]}",
            input=5,
        )
    )

    assert denied["status"] == "denied", denied
    assert denied["reason"] == "tool 'srv/echo' is not granted"
    assert denied["trace"] == []
    assert done["status"] == "done", done
    assert done["output"] == 10, done
    assert [t["decision"] for t in done["trace"]] == ["call"], done


def test_app_node_cannot_reset_parent_call_budget(
    dbos_runtime: None, run_async: Callable[[Awaitable[dict[str, Any]]], dict[str, Any]]
) -> None:
    # Parent call counts seed the inline app's state (parity with Sub): with
    # maxCalls=1 already consumed by the parent's own call, the agent's first
    # use of the same tool is denied instead of starting from a fresh budget.
    frozen = freeze(
        seq(
            call(mcp("srv", "double")),
            app("dbos_seed_ctrl", tools=["srv/double"], budget=Budget(cost=1000)),
        ),
        _snapshot(),
    )
    res = run_async(
        run_flow_dbos(
            frozen.flow.to_json(),
            manifest_to_json(frozen.manifest),
            session_id=f"appseed-{uuid.uuid4().hex[:8]}",
            input=5,
            max_call_limits={"srv/double": 1},
        )
    )
    assert res["status"] == "denied", res
    assert res["reason"] == "tool 'srv/double' exceeded maxCalls=1", res
    assert res["trace"] == [], res


def test_gate_inside_agent_subflow_releases(
    dbos_runtime: None, run_async: Callable[[Awaitable[dict[str, Any]]], dict[str, Any]]
) -> None:
    sid = f"agentgate-{uuid.uuid4().hex[:8]}"
    gated_root_id = _subflows()["gated"]["flowJson"]["id"]

    async def main() -> dict[str, Any]:
        task = asyncio.create_task(run_agent_dbos("dbos_gate_ctrl", session_id=sid, input=5))
        await asyncio.sleep(1.0)
        # The gate parks inside the agent segment's workflow (round 0 sub-flow);
        # its cid is session-prefixed by the inline child env.
        await submit_human_dbos(
            sid, f"{sid}-sub-0/{gated_root_id}@1", {"approved": True, "n": 7}
        )
        return await task

    res = run_async(main())
    assert res["status"] == "done", res
    assert res["output"] == {"approved": True, "n": 7}, res
    assert [t["decision"] for t in res["trace"]] == ["sub"], res
