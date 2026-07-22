from __future__ import annotations

import asyncio
import base64
import time
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any
from urllib.parse import quote

import pytest
from temporalio.exceptions import ApplicationError

from julep.contracts import (
    McpAnnotations,
    ToolContract,
    manifest_to_json,
)
from julep.execution import effects, harness
from julep.execution.harness import (
    FlowInput,
    FlowWorkflow,
    AgentInput,
    _TemporalEnv,
    _MCP_PREFLIGHT_CACHE,
    build_flow_input,
    preflightMcp,
)
from julep.execution.policy import ExecutionPolicy
from julep.freeze import CapabilityOverrides, McpServerSnapshot, McpSnapshot, McpToolSpec
from julep.ir import McpTool
from julep.kinds import Effect, Idempotency
from julep.mcp_auth import McpToolListing
from julep.projection import InMemoryProjection, ProjectionEmitter
from julep.freeze import freeze
from julep.dsl import call, ident, sub


@dataclass
class _Config:
    server: str
    url: str
    headers: dict[str, str]
    version: str | None = None


class _Transport:
    def __init__(self, *, schema: dict[str, Any] | None = None) -> None:
        self._configs = {
            "tracker": _Config(
                server="tracker",
                url="https://tracker.example/mcp",
                headers={"Authorization": "secret://tracker-token"},
            )
        }
        self._auth = None
        self.schema = schema or {"type": "object"}
        self.calls = 0

    def _config(self, server: str) -> _Config:
        return self._configs[server]

    async def _resolve_ref(
        self, value: str, run_secrets: dict[str, str] | None
    ) -> str:
        if value == "secret://tracker-token":
            assert run_secrets is not None
            return run_secrets["tracker-token"]
        return value

    async def list_tools(self, server: str, **_kwargs: Any) -> McpToolListing:
        self.calls += 1
        assert server == "tracker"
        return McpToolListing(
            tools={
                "search": {
                    "inputSchema": self.schema,
                    "annotations": {
                        "readOnlyHint": True,
                        "destructiveHint": False,
                        "openWorldHint": False,
                        "idempotentHint": False,
                    },
                }
            },
            protocol_version="2025-06-18",
            server_version="1.0.0",
        )


def _manifest() -> dict[str, Any]:
    annotations = McpAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        open_world_hint=False,
        idempotent_hint=False,
    )
    snapshot = McpSnapshot(
        servers={
            "tracker": McpServerSnapshot(
                server="tracker",
                tools={
                    "search": McpToolSpec(
                        input_schema={"type": "object"},
                        annotations=annotations,
                    )
                },
                protocol_version="2025-06-18",
                server_version="1.0.0",
            )
        }
    )
    result = freeze(
        call(McpTool(server="tracker", tool="search")),
        snapshot,
        CapabilityOverrides(
            contracts={
                "tracker/search": ToolContract(
                    effect=Effect.READ, idempotency=Idempotency.NONE
                )
            }
        ),
    )
    return manifest_to_json(result.manifest)


def _run(
    transport: _Transport,
    *,
    subflows: dict[str, dict[str, Any]] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    effects.configure(
        effects.WorkerContext(
            mcp_transport=transport,
            subflows=subflows or {},
        )
    )
    payload = {
        "workflowId": "run-1",
        "manifestJson": _manifest(),
        "policy": "pin",
        "secrets": {"tracker-token": "tenant-token"},
        **overrides,
    }
    return asyncio.run(preflightMcp(payload))


def _nested_subflows() -> dict[str, dict[str, Any]]:
    return {
        "middle": {
            "flowJson": sub("child").to_json(),
            "manifestJson": {},
        },
        "child": {
            "flowJson": ident().to_json(),
            "manifestJson": _manifest(),
        },
    }


def test_preflight_pins_surface_and_caches_by_sink_value() -> None:
    _MCP_PREFLIGHT_CACHE.clear()
    transport = _Transport()
    result = _run(transport)
    assert result["completed"] is True
    assert result["policy"] == "pin"
    assert result["surfaceDigest"].startswith("sha256:")
    assert transport.calls == 1
    assert _run(transport) == result
    assert transport.calls == 1
    _run(transport, secrets={"tracker-token": "different-token"})
    assert transport.calls == 2


def test_initial_flow_helper_cannot_claim_preflight_is_completed() -> None:
    flow_input = build_flow_input(
        session_id="new-root",
        flow_json=ident().to_json(),
        manifest_json={},
        secrets={"tracker-token": "tenant-token"},
        mcp_preflight={
            "policy": "off",
            "completed": True,
            "surfaceDigest": "sha256:forged",
        },
    )
    assert flow_input.mcp_preflight == {
        "policy": "off",
        "completed": False,
        "surfaceDigest": None,
    }


def test_raw_flow_start_refuses_run_secrets_before_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def forbidden_effect(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("raw secret-bearing flow scheduled an effect")

    monkeypatch.setattr(harness.workflow, "execute_activity", forbidden_effect)
    with pytest.raises(ApplicationError) as captured:
        asyncio.run(
            FlowWorkflow().run(
                FlowInput(
                    session_id="raw-flow",
                    flow_json=ident().to_json(),
                    manifest_json={},
                    secrets={"tracker-token": "tenant-token"},
                )
            )
        )

    assert captured.value.type == "invalid_run_secret_binding"
    assert captured.value.non_retryable is True


def test_raw_agent_start_refuses_unbound_run_secrets_before_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def forbidden_effect(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("raw secret-bearing agent scheduled an effect")

    monkeypatch.setattr(harness.workflow, "execute_activity", forbidden_effect)
    with pytest.raises(ApplicationError) as captured:
        asyncio.run(
            harness.AgentWorkflow().run(
                AgentInput(
                    controller="controller",
                    session_id="raw-agent",
                    secrets={"tracker-token": "tenant-token"},
                )
            )
        )

    assert captured.value.type == "invalid_run_secret_binding"
    assert captured.value.non_retryable is True


def test_preflight_cache_prunes_expired_entries_and_bounds_unique_sinks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _MCP_PREFLIGHT_CACHE.clear()
    monkeypatch.setattr(harness, "_MCP_PREFLIGHT_CACHE_MAX_ENTRIES", 2)
    transport = _Transport()
    _MCP_PREFLIGHT_CACHE["expired"] = (
        time.monotonic() - harness._MCP_PREFLIGHT_CACHE_TTL_S - 1,
        {"completed": True},
    )
    inserted: list[str] = []

    for token in ("one", "two", "three"):
        before = set(_MCP_PREFLIGHT_CACHE)
        _run(transport, secrets={"tracker-token": token})
        added = set(_MCP_PREFLIGHT_CACHE) - before
        assert len(added) == 1
        inserted.extend(added)

    assert "expired" not in _MCP_PREFLIGHT_CACHE
    assert len(_MCP_PREFLIGHT_CACHE) == 2
    assert inserted[0] not in _MCP_PREFLIGHT_CACHE
    assert set(inserted[1:]) == set(_MCP_PREFLIGHT_CACHE)


def test_preflight_rejects_unused_run_binding_before_discovery() -> None:
    _MCP_PREFLIGHT_CACHE.clear()
    transport = _Transport()
    with pytest.raises(ApplicationError) as captured:
        _run(transport, secrets={"unused": "value"})
    assert captured.value.type == "invalid_run_secret_binding"
    assert transport.calls == 0
    assert "value" not in str(captured.value)


def test_preflight_reports_typed_surface_mismatch() -> None:
    _MCP_PREFLIGHT_CACHE.clear()
    transport = _Transport(schema={"type": "string"})
    with pytest.raises(ApplicationError) as captured:
        _run(transport)
    assert captured.value.type == "tool_surface_mismatch"
    assert "definition_hash" in str(captured.value)


def test_preflight_surface_mismatch_scrubs_reflected_run_secret() -> None:
    _MCP_PREFLIGHT_CACHE.clear()
    secret = "tenant token:/"
    variants = (
        secret,
        base64.b64encode(secret.encode()).decode(),
        quote(secret, safe=""),
    )
    transport = _Transport(
        schema={"type": "string", "description": " | ".join(variants)}
    )
    with pytest.raises(ApplicationError) as captured:
        _run(transport, secrets={"tracker-token": secret})
    serialized = str(captured.value)
    assert captured.value.type == "tool_surface_mismatch"
    assert all(variant not in serialized for variant in variants)


def test_preflight_rejects_all_run_bindings_when_release_has_no_mcp_tools() -> None:
    effects.configure(effects.WorkerContext())
    with pytest.raises(ApplicationError) as captured:
        asyncio.run(
            preflightMcp(
                {
                    "workflowId": "run-no-mcp",
                    "manifestJson": {},
                    "policy": "off",
                    "secrets": {"unused": "value"},
                }
            )
        )
    assert captured.value.type == "invalid_run_secret_binding"
    assert "value" not in str(captured.value)


def test_preflight_off_without_bindings_needs_no_transport() -> None:
    async def unused_caller(*_args: Any) -> Any:
        raise AssertionError("off preflight attempted MCP IO")

    effects.configure(effects.WorkerContext(mcp_call=unused_caller))
    result = asyncio.run(
        preflightMcp(
            {
                "workflowId": "run-off",
                "manifestJson": _manifest(),
                "policy": "off",
            }
        )
    )
    assert result["policy"] == "off"
    assert result["completed"] is True
    assert result["surfaceDigest"].startswith("sha256:")


def test_preflight_off_with_bindings_still_requires_configured_transport() -> None:
    effects.configure(effects.WorkerContext())
    with pytest.raises(ApplicationError, match="MCP transport"):
        asyncio.run(
            preflightMcp(
                {
                    "workflowId": "run-off-binding",
                    "manifestJson": _manifest(),
                    "policy": "off",
                    "secrets": {"tracker-token": "tenant-token"},
                }
            )
        )


def test_preflight_includes_transitively_referenced_subflow_surface() -> None:
    _MCP_PREFLIGHT_CACHE.clear()
    transport = _Transport()

    result = _run(
        transport,
        subflows=_nested_subflows(),
        flowJson=sub("middle").to_json(),
        manifestJson={},
    )

    assert result["completed"] is True
    assert result["surfaceDigest"].startswith("sha256:")
    assert transport.calls == 1


def test_preflight_rejects_binding_unused_by_root_and_referenced_children() -> None:
    _MCP_PREFLIGHT_CACHE.clear()
    transport = _Transport()

    with pytest.raises(ApplicationError) as captured:
        _run(
            transport,
            subflows=_nested_subflows(),
            flowJson=sub("middle").to_json(),
            manifestJson={},
            secrets={"unused": "value"},
        )

    assert captured.value.type == "invalid_run_secret_binding"
    assert transport.calls == 0
    assert "value" not in str(captured.value)


def test_transitive_surface_drift_refuses_before_root_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _MCP_PREFLIGHT_CACHE.clear()
    transport = _Transport(schema={"type": "string"})
    effects.configure(
        effects.WorkerContext(
            mcp_transport=transport,
            subflows=_nested_subflows(),
        )
    )
    activities: list[str] = []
    children: list[Any] = []

    async def fake_execute_activity(fn: Any, payload: Any, **_kwargs: Any) -> Any:
        activities.append(fn.__name__)
        if fn.__name__ == "preflightMcp":
            return await preflightMcp(payload)
        raise AssertionError(f"effect scheduled after rejecting preflight: {fn.__name__}")

    async def fake_execute_child_workflow(
        _fn: Any, child_input: Any, **_kwargs: Any
    ) -> Any:
        children.append(child_input)
        raise AssertionError("child started after rejecting preflight")

    monkeypatch.setattr(harness.workflow, "patched", lambda _patch: True)
    monkeypatch.setattr(
        harness.workflow,
        "info",
        lambda: SimpleNamespace(workflow_id="run-transitive-drift"),
    )
    monkeypatch.setattr(
        harness.workflow,
        "execute_activity",
        fake_execute_activity,
    )
    monkeypatch.setattr(
        harness.workflow,
        "execute_child_workflow",
        fake_execute_child_workflow,
    )

    with pytest.raises(ApplicationError) as captured:
        asyncio.run(
            FlowWorkflow().run(
                FlowInput(
                    session_id="run-transitive-drift",
                    input={"q": "x"},
                    flow_json=sub("middle").to_json(),
                    manifest_json={},
                    max_call_limits={},
                    secrets={"tracker-token": "tenant-token"},
                    mcp_preflight={
                        "policy": "pin",
                        "completed": False,
                        "surfaceDigest": None,
                    },
                )
            )
        )

    assert captured.value.type == "tool_surface_mismatch"
    assert activities == ["preflightMcp"]
    assert children == []


def test_completed_preflight_state_is_carried_to_flow_and_agent_children(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = {
        "policy": "pin",
        "completed": True,
        "surfaceDigest": "sha256:" + "a" * 64,
    }
    children: list[Any] = []

    async def fake_execute_child_workflow(
        _fn: Any, child_input: Any, **_kwargs: Any
    ) -> Any:
        children.append(child_input)
        return {}

    async def fake_execute_activity(
        _fn: Any, _payload: Any, **_kwargs: Any
    ) -> None:
        return None

    async def gate(value: Any, _cid: str, _timeout_s: int | None) -> Any:
        return value

    monkeypatch.setattr(
        harness.workflow,
        "execute_child_workflow",
        fake_execute_child_workflow,
    )
    monkeypatch.setattr(
        harness.workflow,
        "execute_activity",
        fake_execute_activity,
    )
    env = _TemporalEnv(
        manifest={},
        emitter=ProjectionEmitter(InMemoryProjection()),
        session_id="root",
        manifest_json={},
        policy=ExecutionPolicy(),
        gate_waiter=gate,
        mcp_preflight=state,
    )

    asyncio.run(env.run_sub("child", None, {}, "sub-cid"))
    asyncio.run(env.run_agent("controller", {}, "agent-cid"))

    child_flow, child_agent = children
    assert isinstance(child_flow, FlowInput)
    assert child_flow.mcp_preflight == state
    assert isinstance(child_agent, AgentInput)
    assert child_agent.mcp_preflight == state
