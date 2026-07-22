from __future__ import annotations

import asyncio
import hashlib
import json

import pytest

from julep import HAVE_TEMPORAL
from julep.declarations import declarations_blob, load_declarations
from julep.dotctx import Reasoner, reasoner_to_flow
from julep.dsl import app
from julep.errors import FreezeError
from julep.freeze import McpServerSnapshot, McpSnapshot, McpToolSpec, freeze
from julep.registry import (
    Registry,
    ToolSchemaExpectation,
    scoped_tool_expectation_key,
)


EXPECTED = {
    "type": "object",
    "properties": {"query": {"type": "string"}},
    "required": ["query"],
}


def _frozen():
    reasoner = Reasoner(
        "bound-agent",
        "test:model",
        tools=("search",),
        max_rounds=3,
        reply={
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
        },
        output_retries=1,
    )
    flow = reasoner_to_flow(
        reasoner,
        tool_aliases={"search": "tracker/search-posts"},
    )
    snapshot = McpSnapshot(
        servers={
            "tracker": McpServerSnapshot(
                "tracker",
                {"search-posts": McpToolSpec(input_schema=EXPECTED)},
            )
        }
    )
    expectation = ToolSchemaExpectation(
        key="search",
        input_schema=EXPECTED,
        ctx_path="prompt.ctx",
        description="Search posts.",
    )
    return reasoner, freeze(
        flow,
        snapshot,
        expected_tool_schemas={"search": expectation},
    )


def test_freeze_resolves_alias_and_records_exact_agent_contract() -> None:
    _reasoner, frozen = _frozen()
    flow = frozen.flow
    assert flow.tool_aliases == {"search": "tracker/search-posts"}
    assert flow.tool_defs == [
        {
            "type": "function",
            "function": {
                "name": "search",
                "description": "Search posts.",
                "parameters": EXPECTED,
            },
        }
    ]
    assert set(flow.tool_contracts or {}) == {"search"}
    assert {tool.ref.tool for tool in frozen.manifest.values()} == {"search-posts"}


def test_freeze_rejects_non_exact_tools_pyi_schema() -> None:
    reasoner, _frozen_result = _frozen()
    flow = reasoner_to_flow(
        reasoner,
        tool_aliases={"search": "tracker/search-posts"},
    )
    snapshot = McpSnapshot(
        servers={
            "tracker": McpServerSnapshot(
                "tracker",
                {
                    "search-posts": McpToolSpec(
                        input_schema={
                            **EXPECTED,
                            "additionalProperties": False,
                        }
                    )
                },
            )
        }
    )
    with pytest.raises(FreezeError, match="TOOL_SCHEMA_DRIFT.*alias 'search'"):
        freeze(
            flow,
            snapshot,
            expected_tool_schemas={
                "search": ToolSchemaExpectation("search", EXPECTED, "prompt.ctx")
            },
        )


def test_freeze_preserves_legacy_wire_grant_without_alias_map() -> None:
    snapshot = McpSnapshot(
        servers={
            "tracker": McpServerSnapshot(
                "tracker",
                {"search-posts": McpToolSpec(input_schema=EXPECTED)},
            )
        }
    )

    frozen = freeze(app("legacy", tools=["tracker/search-posts"]), snapshot)

    assert frozen.flow.tools == ["tracker/search-posts"]
    assert frozen.flow.tool_aliases is None


def test_freeze_rejects_non_bare_explicit_provider_alias() -> None:
    snapshot = McpSnapshot(
        servers={
            "tracker": McpServerSnapshot(
                "tracker",
                {"search-posts": McpToolSpec(input_schema=EXPECTED)},
            )
        }
    )
    flow = app(
        "aliased",
        tools=["tracker/search-posts"],
        tool_aliases={"tracker/search-posts": "tracker/search-posts"},
    )

    with pytest.raises(FreezeError, match="provider tool alias"):
        freeze(flow, snapshot)


def test_declarations_v2_carries_frozen_agent_and_loads_release_scoped() -> None:
    reasoner, frozen = _frozen()
    blob = declarations_blob([reasoner], registry=Registry(), flow=frozen.flow)
    payload = json.loads(blob)
    assert payload["schemaVersion"] == 2
    spec = payload["agents"]["bound-agent"]
    assert spec["toolAliases"] == {"search": "tracker/search-posts"}
    assert spec["grantedTools"] == ["search"]
    assert spec["toolDefs"][0]["function"]["parameters"] == EXPECTED

    target = Registry()
    digest = "sha256:" + hashlib.sha256(blob).hexdigest()
    load_declarations(
        blob,
        expected_hash=digest,
        registry=target,
        release_scoped=True,
    )
    assert target.get_reasoner("bound-agent") == reasoner
    assert target.agent_specs["bound-agent"]["toolAliases"] == {
        "search": "tracker/search-posts"
    }


def test_release_scoped_declarations_allow_conflicting_logical_reasoners() -> None:
    first = Reasoner("shared", "test:first")
    second = Reasoner("shared", "test:second")
    first_blob = declarations_blob([first], registry=Registry())
    second_blob = declarations_blob([second], registry=Registry())

    first_registry = Registry()
    second_registry = Registry()
    load_declarations(
        first_blob,
        expected_hash="sha256:" + hashlib.sha256(first_blob).hexdigest(),
        registry=first_registry,
        release_scoped=True,
    )
    load_declarations(
        second_blob,
        expected_hash="sha256:" + hashlib.sha256(second_blob).hexdigest(),
        registry=second_registry,
        release_scoped=True,
    )

    assert first_registry.get_reasoner("shared").model == "test:first"
    assert second_registry.get_reasoner("shared").model == "test:second"


def test_registry_scopes_reused_bare_tool_aliases_by_reasoner() -> None:
    registry = Registry()
    first = ToolSchemaExpectation("search", EXPECTED, "first/tools.pyi")
    second_schema = {
        "type": "object",
        "properties": {"id": {"type": "integer"}},
        "required": ["id"],
    }
    second = ToolSchemaExpectation("search", second_schema, "second/tools.pyi")
    registry.register_tool_expectation(first, scope="first")
    registry.register_tool_expectation(second, scope="second")

    assert registry.tool_expectations[scoped_tool_expectation_key("first", "search")] == first
    assert registry.tool_expectations[scoped_tool_expectation_key("second", "search")] == second


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_agent_workflow_dispatches_bare_alias_to_wire_tool(monkeypatch) -> None:
    from julep.execution import harness
    from julep.execution.harness import AgentInput, AgentWorkflow

    monkeypatch.setattr(
        harness, "_agent_frozen_tool_input_validation_enabled", lambda: True
    )

    rounds = iter(
        [
            {
                "tool_calls": [
                    {"id": "tool-1", "tool": "search", "input": {"query": "q"}}
                ]
            },
            {"output": {"answer": "done"}},
        ]
    )
    calls = []

    async def fake_execute_activity(fn, payload=None, **kwargs):
        name = fn.__name__
        if name == "invokeReasoner":
            return next(rounds)
        if name == "callTool":
            calls.append(payload)
            return ["post-1"]
        if name == "validateAgentOutput":
            return None
        return None

    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)
    inp = AgentInput(
        controller="bound-agent",
        session_id="alias-run",
        input={"query": "q"},
        config={
            "maxRounds": 3,
            "nativeTools": True,
            "replySchema": {
                "type": "object",
                "properties": {"answer": {"type": "string"}},
                "required": ["answer"],
            },
        },
        granted_tools=["search"],
        granted_contracts={
            "search": {"effect": "read", "idempotency": "native", "asserted": True}
        },
        tool_defs=[
            {
                "type": "function",
                "function": {"name": "search", "description": "", "parameters": EXPECTED},
            }
        ],
        tool_aliases={"search": "tracker/search-posts"},
        resolve_spec=False,
    )
    result = asyncio.run(AgentWorkflow().run(inp))
    assert result["status"] == "done"
    assert calls[0].tool_ref == {
        "kind": "mcp",
        "server": "tracker",
        "tool": "search-posts",
    }
    assert result["trace"][0]["callId"] == "tool-1"
    assert result["trace"][0]["arguments"] == {"query": "q"}


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
@pytest.mark.parametrize("call_count", [1, 2], ids=["sequential", "concurrent-read"])
def test_agent_workflow_reraises_typed_tool_surface_drift(
    monkeypatch,
    call_count: int,
) -> None:
    from temporalio.exceptions import ActivityError, ApplicationError

    from julep.execution import harness
    from julep.execution.harness import AgentInput, AgentWorkflow

    monkeypatch.setattr(
        harness, "_agent_frozen_tool_input_validation_enabled", lambda: True
    )

    async def fake_execute_activity(fn, payload=None, **kwargs):
        if fn.__name__ == "invokeReasoner":
            calls = [
                {
                    "id": f"tool-{index}",
                    "tool": "search",
                    "input": {"query": f"q-{index}"},
                }
                for index in range(call_count)
            ]
            return calls[0] if call_count == 1 else {"tool_calls": calls}
        if fn.__name__ == "callTool":
            cause = ApplicationError(
                "MCP tool surface drift for tracker/search-posts: tool not found",
                type="ToolSurfaceDrift",
                non_retryable=True,
            )
            activity_error = ActivityError(
                "tool call failed",
                scheduled_event_id=1,
                started_event_id=2,
                identity="worker",
                activity_type="callTool",
                activity_id="activity-1",
                retry_state=None,
            )
            raise activity_error from cause
        return None

    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)
    inp = AgentInput(
        controller="bound-agent",
        session_id=f"drift-{call_count}",
        input={"query": "q"},
        config={"maxRounds": 3, "nativeTools": True},
        granted_tools=["search"],
        granted_contracts={
            "search": {"effect": "read", "idempotency": "native", "asserted": True}
        },
        tool_defs=[
            {
                "type": "function",
                "function": {"name": "search", "description": "", "parameters": EXPECTED},
            }
        ],
        tool_aliases={"search": "tracker/search-posts"},
        resolve_spec=False,
    )

    with pytest.raises(ApplicationError) as raised:
        asyncio.run(AgentWorkflow().run(inp))
    assert raised.value.type == "ToolSurfaceDrift"
    assert raised.value.non_retryable is True


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
@pytest.mark.parametrize("batched", [False, True], ids=["single", "call-many"])
def test_agent_validates_frozen_tool_inputs_before_dispatch(
    monkeypatch,
    batched: bool,
) -> None:
    from julep.execution import harness
    from julep.execution.harness import AgentInput, AgentWorkflow
    from julep.execution.llm import json_schema_error

    monkeypatch.setattr(
        harness, "_agent_frozen_tool_input_validation_enabled", lambda: True
    )

    if batched:
        rounds = iter(
            [
                {
                    "tool_calls": [
                        {"id": "ok-skipped", "tool": "search", "input": {"query": "ok"}},
                        {"id": "bad", "tool": "search", "input": {"query": 7}},
                    ]
                },
                {
                    "tool_calls": [
                        {"id": "ok-1", "tool": "search", "input": {"query": "one"}},
                        {"id": "ok-2", "tool": "search", "input": {"query": "two"}},
                    ]
                },
                {"output": {"answer": "done"}},
            ]
        )
    else:
        rounds = iter(
            [
                {"id": "bad", "tool": "search", "input": {"query": 7}},
                {"id": "ok-1", "tool": "search", "input": {"query": "one"}},
                {"output": {"answer": "done"}},
            ]
        )
    calls = []

    async def fake_execute_activity(fn, payload=None, **kwargs):
        if fn.__name__ == "invokeReasoner":
            return next(rounds)
        if fn.__name__ == "validateJsonSchema":
            return json_schema_error(payload.value, payload.schema)
        if fn.__name__ == "callTool":
            calls.append(payload)
            return []
        return None

    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)
    inp = AgentInput(
        controller="bound-agent",
        session_id=f"schema-gate-{batched}",
        input={"query": "start"},
        config={"maxRounds": 5, "nativeTools": True},
        granted_tools=["search"],
        granted_contracts={
            "search": {"effect": "read", "idempotency": "native", "asserted": True}
        },
        tool_defs=[
            {
                "type": "function",
                "function": {"name": "search", "description": "", "parameters": EXPECTED},
            }
        ],
        tool_aliases={"search": "tracker/search-posts"},
        resolve_spec=False,
    )

    result = asyncio.run(AgentWorkflow().run(inp))
    assert result["status"] == "done"
    assert len(calls) == (2 if batched else 1)
    assert all(call.input_schema_validated is True for call in calls)
    assert all(call.value["query"] != 7 for call in calls)
    assert result["trace"][0]["decision"] == "tool_input_reask"
    assert result["trace"][0]["arguments"] == {"query": 7}


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_agent_legacy_replay_branch_dispatches_without_new_validation_activity(
    monkeypatch,
) -> None:
    from julep.execution import harness
    from julep.execution.harness import AgentInput, AgentWorkflow

    monkeypatch.setattr(
        harness, "_agent_frozen_tool_input_validation_enabled", lambda: False
    )
    rounds = iter(
        [
            {"id": "legacy-call", "tool": "search", "input": {"query": 7}},
            {"output": {"answer": "done"}},
        ]
    )
    calls = []

    async def fake_execute_activity(fn, payload=None, **kwargs):
        if fn.__name__ == "invokeReasoner":
            return next(rounds)
        if fn.__name__ == "validateJsonSchema":
            raise AssertionError("legacy replay branch scheduled a new validation activity")
        if fn.__name__ == "callTool":
            calls.append(payload)
            return []
        return None

    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)
    inp = AgentInput(
        controller="bound-agent",
        session_id="legacy-schema-gate",
        input={"query": "start"},
        config={"maxRounds": 3, "nativeTools": True},
        granted_tools=["search"],
        granted_contracts={
            "search": {"effect": "read", "idempotency": "native", "asserted": True}
        },
        tool_defs=[
            {
                "type": "function",
                "function": {"name": "search", "description": "", "parameters": EXPECTED},
            }
        ],
        tool_aliases={"search": "tracker/search-posts"},
        resolve_spec=False,
    )

    result = asyncio.run(AgentWorkflow().run(inp))
    assert result["status"] == "done"
    assert len(calls) == 1
    assert calls[0].value == {"query": 7}
    assert calls[0].input_schema_validated is False
    assert result["trace"][0]["decision"] == "call"
