"""CMA agent-loop driver tests."""

from __future__ import annotations

from typing import Any

import pytest

from composable_agents import AgentConfig, Budget, EnforcementMode, app
from composable_agents.agent_loop import drive_agent_loop
from composable_agents.execution.cma import (
    CMAAgentEnv,
    CMAEvent,
    drive_cma_agent_loop,
    manifest_to_custom_tools,
)
from composable_agents.execution.interpreter import InMemoryEnv, interpret
from composable_agents.projection import InMemoryProjection, ProjectionEmitter
from cma_fakes import FakeCMAClient, FakeCMASession
from conftest import run


def test_cross_parity_with_local_agent_loop() -> None:
    replies = iter([
        {"tool": "search"},
        {"tool": "fetch"},
        {"output": {"answer": 42}},
    ])

    async def invoke_controller(_payload: dict[str, Any]) -> dict[str, Any]:
        return next(replies)

    async def local_call_tool(tool: str, _value: Any) -> str:
        return {"search": "r1", "fetch": "r2"}[tool]

    local = run(
        drive_agent_loop(
            input="q",
            cfg=AgentConfig(),
            invoke_controller=invoke_controller,
            call_tool=local_call_tool,
            granted={"search", "fetch"},
        )
    )

    session = FakeCMASession([
        CMAEvent("custom_tool_use", tool="search", input=None, call_id="e1"),
        CMAEvent("custom_tool_use", tool="fetch", input=None, call_id="e2"),
        CMAEvent("terminal", output={"answer": 42}),
    ])

    async def cma_call_tool(tool: str, _value: Any, _cid: str) -> str:
        return {"search": "r1", "fetch": "r2"}[tool]

    cma = run(
        drive_cma_agent_loop(
            input="q",
            cfg=AgentConfig(),
            session=session,
            call_tool=cma_call_tool,
            granted={"search", "fetch"},
        )
    )

    assert cma == local


def test_terminal_event_honors_max_rounds_zero_parity_with_local_agent_loop() -> None:
    async def invoke_controller(_payload: dict[str, Any]) -> dict[str, Any]:
        return {"output": {"answer": 42}}

    async def local_call_tool(_tool: str, _value: Any) -> Any:
        raise AssertionError("tool should not execute")

    cfg = AgentConfig(max_rounds=0)
    local = run(
        drive_agent_loop(
            input="q",
            cfg=cfg,
            invoke_controller=invoke_controller,
            call_tool=local_call_tool,
        )
    )

    session = FakeCMASession([CMAEvent("terminal", output={"answer": 42})])

    async def cma_call_tool(_tool: str, _value: Any, _cid: str) -> Any:
        raise AssertionError("tool should not execute")

    cma = run(
        drive_cma_agent_loop(
            input="q",
            cfg=cfg,
            session=session,
            call_tool=cma_call_tool,
        )
    )

    assert local["status"] == "max_rounds"
    assert local["cost"] == 0.0
    assert cma == local


def test_terminal_event_honors_budget_precheck_parity_with_local_agent_loop() -> None:
    async def invoke_controller(_payload: dict[str, Any]) -> dict[str, Any]:
        return {"output": {"answer": 42}}

    async def local_call_tool(_tool: str, _value: Any) -> Any:
        raise AssertionError("tool should not execute")

    cfg = AgentConfig(budget=Budget(cost=0.5))
    local = run(
        drive_agent_loop(
            input="q",
            cfg=cfg,
            invoke_controller=invoke_controller,
            call_tool=local_call_tool,
        )
    )

    session = FakeCMASession([CMAEvent("terminal", output={"answer": 42})])

    async def cma_call_tool(_tool: str, _value: Any, _cid: str) -> Any:
        raise AssertionError("tool should not execute")

    cma = run(
        drive_cma_agent_loop(
            input="q",
            cfg=cfg,
            session=session,
            call_tool=cma_call_tool,
        )
    )

    assert local["status"] == "over_budget"
    assert local["cost"] == 0.0
    assert cma == local


def test_terminal_after_tool_honors_max_rounds_parity_with_local_agent_loop() -> None:
    replies = iter([
        {"tool": "search"},
        {"output": {"answer": 42}},
    ])

    async def invoke_controller(_payload: dict[str, Any]) -> dict[str, Any]:
        return next(replies)

    async def local_call_tool(_tool: str, value: Any) -> dict[str, Any]:
        return {"searched": value}

    cfg = AgentConfig(max_rounds=1)
    local = run(
        drive_agent_loop(
            input="q",
            cfg=cfg,
            invoke_controller=invoke_controller,
            call_tool=local_call_tool,
            granted={"search"},
        )
    )

    session = FakeCMASession([
        CMAEvent("custom_tool_use", tool="search", input=None, call_id="e1"),
        CMAEvent("terminal", output={"answer": 42}),
    ])

    async def cma_call_tool(_tool: str, value: Any, _cid: str) -> dict[str, Any]:
        return {"searched": value}

    cma = run(
        drive_cma_agent_loop(
            input="q",
            cfg=cfg,
            session=session,
            call_tool=cma_call_tool,
            granted={"search"},
        )
    )

    assert local["status"] == "max_rounds"
    assert cma == local


def test_ungranted_tool_strict_denies_and_sends_tool_error() -> None:
    session = FakeCMASession([
        CMAEvent("custom_tool_use", tool="secret", input={}, call_id="e1"),
    ])

    async def call_tool(_tool: str, _value: Any, _cid: str) -> Any:
        raise AssertionError("tool should not execute")

    out = run(
        drive_cma_agent_loop(
            input="q",
            cfg=AgentConfig(),
            session=session,
            call_tool=call_tool,
            granted={"search"},
        )
    )

    assert out["status"] == "denied"
    assert "secret" in out["reason"]
    assert session.errors == [("e1", out["reason"])]
    assert session.cancelled >= 1


def test_tool_error_failure_does_not_mask_strict_denial() -> None:
    class RaisingToolErrorSession(FakeCMASession):
        async def tool_error(self, call_id: str, reason: str) -> None:
            await super().tool_error(call_id, reason)
            raise RuntimeError("notify failed")

    session = RaisingToolErrorSession([
        CMAEvent("custom_tool_use", tool="secret", input={}, call_id="e1"),
    ])

    async def call_tool(_tool: str, _value: Any, _cid: str) -> Any:
        raise AssertionError("tool should not execute")

    out = run(
        drive_cma_agent_loop(
            input="q",
            cfg=AgentConfig(),
            session=session,
            call_tool=call_tool,
            granted={"search"},
        )
    )

    assert out["status"] == "denied"
    assert "secret" in out["reason"]


def test_ungranted_tool_dev_warns_but_executes() -> None:
    session = FakeCMASession([
        CMAEvent("custom_tool_use", tool="secret", input={"q": "x"}, call_id="e1"),
        CMAEvent("terminal", output="done"),
    ])

    async def call_tool(tool: str, value: Any, _cid: str) -> dict[str, Any]:
        return {"tool": tool, "value": value}

    out = run(
        drive_cma_agent_loop(
            input="q",
            cfg=AgentConfig(mode=EnforcementMode.DEV),
            session=session,
            call_tool=call_tool,
            granted={"search"},
        )
    )

    assert out["status"] == "done"
    assert out["prodGap"]
    assert session.results == [("e1", {"tool": "secret", "value": {"q": "x"}})]


def test_max_calls_exceeded_strict_denies_second_call() -> None:
    session = FakeCMASession([
        CMAEvent("custom_tool_use", tool="search", input=None, call_id="e1"),
        CMAEvent("custom_tool_use", tool="search", input=None, call_id="e2"),
    ])

    async def call_tool(_tool: str, value: Any, _cid: str) -> Any:
        return value

    out = run(
        drive_cma_agent_loop(
            input="q",
            cfg=AgentConfig(),
            session=session,
            call_tool=call_tool,
            granted={"search"},
            contracts={"search": {"maxCalls": 1}},
        )
    )

    assert out["status"] == "denied"
    assert "maxCalls=1" in out["reason"]
    assert session.results == [("e1", "q")]
    assert session.errors == [("e2", out["reason"])]


def test_tool_result_failure_returns_controller_error() -> None:
    class RaisingToolResultSession(FakeCMASession):
        async def tool_result(self, call_id: str, result: Any) -> None:
            await super().tool_result(call_id, result)
            raise RuntimeError("delivery failed")

    session = RaisingToolResultSession([
        CMAEvent("custom_tool_use", tool="search", input=None, call_id="e1"),
        CMAEvent("terminal", output="done"),
    ])

    async def call_tool(_tool: str, value: Any, _cid: str) -> Any:
        return value

    out = run(
        drive_cma_agent_loop(
            input="q",
            cfg=AgentConfig(),
            session=session,
            call_tool=call_tool,
            granted={"search"},
        )
    )

    assert out["status"] == "controller_error"
    assert "deliver tool result" in out["reason"]
    assert session.results == [("e1", "q")]


def test_over_budget_from_action_guard() -> None:
    session = FakeCMASession([
        CMAEvent("custom_tool_use", tool="search", input=None, call_id="e1"),
    ])

    async def call_tool(_tool: str, _value: Any, _cid: str) -> Any:
        raise AssertionError("tool should not execute")

    out = run(
        drive_cma_agent_loop(
            input="q",
            cfg=AgentConfig(budget=Budget(cost=0.75), think_cost=0.25),
            session=session,
            call_tool=call_tool,
            granted={"search"},
        )
    )

    assert out["status"] == "over_budget"
    assert session.results == []


def test_max_rounds_denies_second_tool_use() -> None:
    session = FakeCMASession([
        CMAEvent("custom_tool_use", tool="search", input=None, call_id="e1"),
        CMAEvent("custom_tool_use", tool="fetch", input=None, call_id="e2"),
    ])

    async def call_tool(_tool: str, value: Any, _cid: str) -> Any:
        return value

    out = run(
        drive_cma_agent_loop(
            input="q",
            cfg=AgentConfig(max_rounds=1),
            session=session,
            call_tool=call_tool,
            granted={"search", "fetch"},
        )
    )

    assert out["status"] == "max_rounds"
    assert session.results == [("e1", "q")]


def test_call_cids_are_deterministic() -> None:
    seen: list[str] = []
    session = FakeCMASession([
        CMAEvent("custom_tool_use", tool="search", input=None, call_id="e1"),
        CMAEvent("custom_tool_use", tool="fetch", input=None, call_id="e2"),
        CMAEvent("terminal", output="done"),
    ])

    async def call_tool(_tool: str, value: Any, cid: str) -> Any:
        seen.append(cid)
        return value

    run(
        drive_cma_agent_loop(
            input="q",
            cfg=AgentConfig(),
            session=session,
            call_tool=call_tool,
            granted={"search", "fetch"},
            session_cid="sess",
        )
    )

    assert seen == ["sess-call-0", "sess-call-1"]


def test_cancels_session_when_event_stream_raises() -> None:
    session = FakeCMASession(
        [CMAEvent("custom_tool_use", tool="search", input=None, call_id="e1")],
        raise_after=0,
    )

    async def call_tool(_tool: str, value: Any, _cid: str) -> Any:
        return value

    with pytest.raises(RuntimeError):
        run(
            drive_cma_agent_loop(
                input="q",
                cfg=AgentConfig(),
                session=session,
                call_tool=call_tool,
                granted={"search"},
            )
        )

    assert session.cancelled >= 1


def test_cma_agent_env_runs_app_node_end_to_end() -> None:
    flow = app("controller", tools=["search"])
    session = FakeCMASession([
        CMAEvent("custom_tool_use", tool="search", input=None, call_id="e1"),
        CMAEvent("terminal", output={"answer": 42}),
    ])
    client = FakeCMAClient(session)
    inner = InMemoryEnv({}, ProjectionEmitter(InMemoryProjection()))
    env = CMAAgentEnv(
        inner,
        client=client,
        environment={"kind": "fake"},
        hands={"search": lambda value: {"searched": value}},
        cfg=AgentConfig(),
        granted={"search"},
    )

    out = run(interpret(flow, "q", env))

    assert out.value["status"] == "done"
    assert out.value["output"] == {"answer": 42}
    assert client.agent == {
        "name": "controller",
        "tools": manifest_to_custom_tools(["search"]),
    }
    assert client.input == "q"
    assert client.environment == {"kind": "fake"}
    assert client.session_cid is not None


def test_cma_agent_env_unconstrained_projects_all_hands_and_grants_project_subset() -> None:
    inner = InMemoryEnv({}, ProjectionEmitter(InMemoryProjection()))

    unconstrained_session = FakeCMASession([CMAEvent("terminal", output="done")])
    unconstrained_client = FakeCMAClient(unconstrained_session)
    unconstrained_env = CMAAgentEnv(
        inner,
        client=unconstrained_client,
        hands={"a": lambda value: value, "b": lambda value: value},
        cfg=AgentConfig(),
        granted=None,
        custom_tools=None,
    )

    run(unconstrained_env.run_agent("controller", "q", "cid-unconstrained"))

    assert unconstrained_client.agent is not None
    assert unconstrained_client.agent["tools"] == manifest_to_custom_tools(["a", "b"])
    assert all(tool["type"] == "custom" for tool in unconstrained_client.agent["tools"])

    constrained_session = FakeCMASession([CMAEvent("terminal", output="done")])
    constrained_client = FakeCMAClient(constrained_session)
    constrained_env = CMAAgentEnv(
        inner,
        client=constrained_client,
        hands={"a": lambda value: value, "b": lambda value: value},
        cfg=AgentConfig(),
        granted={"a"},
        custom_tools=None,
    )

    run(constrained_env.run_agent("controller", "q", "cid-constrained"))

    assert constrained_client.agent is not None
    assert constrained_client.agent["tools"] == manifest_to_custom_tools(["a"])


def test_manifest_to_custom_tools_shape_order_and_no_builtins() -> None:
    tools = manifest_to_custom_tools(
        ["search", "fetch"],
        input_schemas={"fetch": {"type": "object", "properties": {"url": {"type": "string"}}}},
        descriptions={"search": "Search the web"},
    )

    assert tools == [
        {
            "type": "custom",
            "name": "search",
            "description": "Search the web",
            "input_schema": {"type": "object"},
        },
        {
            "type": "custom",
            "name": "fetch",
            "description": "",
            "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}},
        },
    ]
    assert all(tool["name"] != "agent_toolset_20260401" for tool in tools)
