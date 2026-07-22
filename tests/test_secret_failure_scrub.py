from __future__ import annotations

import asyncio
import base64
import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import pytest
from temporalio.api.failure.v1 import Failure
from temporalio.converter import DefaultFailureConverter, DefaultPayloadConverter
from temporalio.exceptions import ApplicationError

from julep import arr
from julep.contracts import McpAnnotations, ToolContract, manifest_to_json
from julep.dotctx import Reasoner
from julep.dsl import call
from julep.errors import ToolSurfaceDrift
from julep.execution import activities, effects, harness, reasoner_batch
from julep.execution.blobstore import InMemoryBlobStore
from julep.execution.failure_scrub import application_error_from_failure
from julep.execution.harness import FlowInput, FlowWorkflow
from julep.freeze import (
    CapabilityOverrides,
    McpServerSnapshot,
    McpSnapshot,
    McpToolSpec,
    freeze,
)
from julep.ir import McpTool
from julep.kinds import Effect, Idempotency
from julep.purity import register_pure
from julep.registry import Registry
from julep.secrets import register_secret_value
from julep.trajectory import InMemoryTrajectoryStore


SECRET = "tenant: token/with space"
VARIANTS = (
    SECRET,
    base64.b64encode(SECRET.encode()).decode(),
    quote(SECRET, safe=""),
)
ECHO = " | ".join(VARIANTS)
OPERATOR_SECRET = "operator: vault/with space"
OPERATOR_VARIANTS = (
    OPERATOR_SECRET,
    base64.b64encode(OPERATOR_SECRET.encode()).decode(),
    quote(OPERATOR_SECRET, safe=""),
)
OPERATOR_ECHO = " | ".join(OPERATOR_VARIANTS)


def _assert_variants_safe(value: Any, variants: tuple[str, ...]) -> None:
    serialized = value if isinstance(value, bytes) else str(value).encode()
    for variant in variants:
        assert variant.encode() not in serialized


def _assert_safe(value: Any) -> None:
    _assert_variants_safe(value, VARIANTS)


def _serialized_failure(error: BaseException) -> bytes:
    failure = Failure()
    DefaultFailureConverter().to_failure(
        error,
        DefaultPayloadConverter(),
        failure,
    )
    return failure.SerializeToString()


@pytest.fixture(autouse=True)
def _reset_worker_context() -> Any:
    effects.configure(effects.WorkerContext())
    harness._MCP_PREFLIGHT_CACHE.clear()
    yield
    effects.configure(effects.WorkerContext())
    harness._MCP_PREFLIGHT_CACHE.clear()


def test_call_tool_failure_is_scrubbed_before_temporal_serialization() -> None:
    async def fail_mcp(*_args: Any) -> Any:
        raise RuntimeError(f"remote echoed {ECHO}")

    effects.configure(effects.WorkerContext(mcp_call=fail_mcp))
    inp = activities.CallToolInput(
        tool_ref={"kind": "mcp", "server": "srv", "tool": "search"},
        value={"q": "hi"},
        cid="call-1",
        secrets={"tenant-token": SECRET},
    )

    with pytest.raises(ApplicationError) as raised:
        asyncio.run(activities.callTool(inp))

    assert raised.value.type == "RuntimeError"
    assert raised.value.__suppress_context__ is True
    _assert_safe(str(raised.value))
    _assert_safe(_serialized_failure(raised.value))


def test_invoke_reasoner_failure_is_scrubbed_before_temporal_serialization() -> None:
    registry = Registry()
    registry.register_reasoner(Reasoner(name="secret.fail", model="test", system="s"))

    async def fail_llm(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError(f"provider echoed {ECHO}")

    effects.configure(effects.WorkerContext(llm=fail_llm, registry=registry))
    inp = activities.InvokeReasonerInput(
        reasoner="secret.fail",
        value={"q": "hi"},
        cid="think-1",
        secrets={"tenant-token": SECRET},
    )

    with pytest.raises(ApplicationError) as raised:
        asyncio.run(activities.invokeReasoner(inp))

    assert raised.value.type == "RuntimeError"
    _assert_safe(str(raised.value))
    _assert_safe(_serialized_failure(raised.value))


def test_call_tool_failure_scrubs_operator_variants_without_run_map() -> None:
    register_secret_value(OPERATOR_SECRET)

    async def fail_mcp(*_args: Any) -> Any:
        raise RuntimeError(f"remote echoed {OPERATOR_ECHO}")

    effects.configure(effects.WorkerContext(mcp_call=fail_mcp))
    inp = activities.CallToolInput(
        tool_ref={"kind": "mcp", "server": "srv", "tool": "search"},
        value={"q": "hi"},
        cid="operator-call",
    )

    with pytest.raises(ApplicationError) as raised:
        asyncio.run(activities.callTool(inp))

    _assert_variants_safe(str(raised.value), OPERATOR_VARIANTS)
    _assert_variants_safe(_serialized_failure(raised.value), OPERATOR_VARIANTS)


def test_invoke_reasoner_failure_scrubs_operator_variants_without_run_map() -> None:
    register_secret_value(OPERATOR_SECRET)
    registry = Registry()
    registry.register_reasoner(
        Reasoner(name="operator.fail", model="test", system="s")
    )

    async def fail_llm(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError(f"provider echoed {OPERATOR_ECHO}")

    effects.configure(effects.WorkerContext(llm=fail_llm, registry=registry))
    inp = activities.InvokeReasonerInput(
        reasoner="operator.fail",
        value={"q": "hi"},
        cid="operator-think",
    )

    with pytest.raises(ApplicationError) as raised:
        asyncio.run(activities.invokeReasoner(inp))

    _assert_variants_safe(str(raised.value), OPERATOR_VARIANTS)
    _assert_variants_safe(_serialized_failure(raised.value), OPERATOR_VARIANTS)


def test_compile_plan_failure_scrubs_operator_variants_without_run_map(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    register_secret_value(OPERATOR_SECRET)

    async def fail_plan(_inp: Any) -> Any:
        raise RuntimeError(f"planner echoed {OPERATOR_ECHO}")

    monkeypatch.setattr(effects, "compilePlan", fail_plan)
    inp = activities.CompilePlanInput(
        planner="operator.plan",
        value={"q": "hi"},
        cid="operator-plan",
    )

    with pytest.raises(ApplicationError) as raised:
        asyncio.run(activities.compilePlan(inp))

    _assert_variants_safe(str(raised.value), OPERATOR_VARIANTS)
    _assert_variants_safe(_serialized_failure(raised.value), OPERATOR_VARIANTS)


def test_batch_provider_failure_scrubs_operator_variants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    register_secret_value(OPERATOR_SECRET)

    class _FailingAdapter:
        async def poll_status(self, _batch_id: str) -> str:
            raise RuntimeError(f"batch provider echoed {OPERATOR_ECHO}")

    monkeypatch.setattr(
        reasoner_batch,
        "_provider_adapter_by_name",
        lambda _provider: _FailingAdapter(),
    )

    with pytest.raises(ApplicationError) as raised:
        asyncio.run(
            reasoner_batch.pollBatch(
                reasoner_batch.PollBatchInput(
                    provider="test",
                    batch_id="batch-1",
                )
            )
        )

    _assert_variants_safe(str(raised.value), OPERATOR_VARIANTS)
    _assert_variants_safe(_serialized_failure(raised.value), OPERATOR_VARIANTS)


def test_caught_batch_parse_failure_scrubs_operator_variants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    register_secret_value(OPERATOR_SECRET)

    class _Adapter:
        def results(self, _batch_id: str) -> list[tuple[str, dict[str, Any]]]:
            return [("call-1", {})]

    class _Registry:
        def get_reasoner(self, _name: str) -> object:
            return object()

    def fail_parse(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError(f"batch parser echoed {OPERATOR_ECHO}")

    monkeypatch.setattr(
        reasoner_batch,
        "_provider_adapter_by_name",
        lambda _provider: _Adapter(),
    )
    monkeypatch.setattr(
        effects,
        "_hydrate_runtime_declarations",
        lambda _ref: _Registry(),
    )
    monkeypatch.setattr(reasoner_batch, "_parse_batch_reply", fail_parse)

    result = asyncio.run(
        reasoner_batch.fetchBatchResults(
            reasoner_batch.FetchBatchResultsInput(
                provider="test",
                batch_id="batch-1",
                calls=[
                    reasoner_batch.ReasonerCall(
                        reasoner="test.reasoner",
                        value={},
                        custom_id="call-1",
                    )
                ],
            )
        )
    )

    assert result[0]["error"] is True
    _assert_variants_safe(result[0]["reason"], OPERATOR_VARIANTS)


def test_tool_surface_drift_stays_typed_nonretryable_after_scrubbing() -> None:
    async def drift(*_args: Any) -> Any:
        raise ToolSurfaceDrift("srv", "search", f"tool_not_found {ECHO}")

    effects.configure(effects.WorkerContext(mcp_call=drift))
    inp = activities.CallToolInput(
        tool_ref={"kind": "mcp", "server": "srv", "tool": "search"},
        value={"q": "hi"},
        cid="call-drift",
        secrets={"tenant-token": SECRET},
    )

    with pytest.raises(ApplicationError) as raised:
        asyncio.run(activities.callTool(inp))

    assert raised.value.type == "ToolSurfaceDrift"
    assert raised.value.non_retryable is True
    _assert_safe(str(raised.value))
    _assert_safe(raised.value.details)
    _assert_safe(_serialized_failure(raised.value))


def test_nested_application_error_keeps_type_without_secret_cause() -> None:
    leaf = ApplicationError(
        f"tool denied after echo {ECHO}",
        {"diagnostic": ECHO},
        type="CapabilityDenied",
        non_retryable=True,
    )
    wrapper = RuntimeError("child workflow failed")
    wrapper.__cause__ = leaf

    rebuilt = application_error_from_failure(
        wrapper,
        {"tenant-token": SECRET},
        non_retryable=True,
    )

    assert rebuilt.type == "CapabilityDenied"
    assert rebuilt.non_retryable is True
    assert rebuilt.__cause__ is None
    _assert_safe(str(rebuilt))
    _assert_safe(rebuilt.details)
    _assert_safe(_serialized_failure(rebuilt))


@dataclass
class _McpConfig:
    server: str = "tracker"
    url: str = "https://tracker.example/mcp"
    headers: dict[str, str] | None = None
    version: str | None = None

    def __post_init__(self) -> None:
        self.headers = {"Authorization": "secret://tenant-token"}


class _FailingPreflightTransport:
    _auth = None

    def __init__(self, echo: str = ECHO) -> None:
        self.echo = echo

    def _config(self, _server: str) -> _McpConfig:
        return _McpConfig()

    async def _resolve_ref(self, _value: str, _secrets: Any) -> str:
        raise RuntimeError(f"resolver echoed {self.echo}")


def _mcp_manifest() -> dict[str, Any]:
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
            )
        }
    )
    frozen = freeze(
        call(McpTool(server="tracker", tool="search")),
        snapshot,
        CapabilityOverrides(
            contracts={
                "tracker/search": ToolContract(
                    effect=Effect.READ,
                    idempotency=Idempotency.NONE,
                )
            }
        ),
    )
    return manifest_to_json(frozen.manifest)


def test_preflight_failure_is_scrubbed_before_temporal_serialization() -> None:
    effects.configure(
        effects.WorkerContext(mcp_transport=_FailingPreflightTransport())
    )

    with pytest.raises(ApplicationError) as raised:
        asyncio.run(
            harness.preflightMcp(
                {
                    "workflowId": "preflight-secret",
                    "manifestJson": _mcp_manifest(),
                    "policy": "pin",
                    "secrets": {"tenant-token": SECRET},
                }
            )
        )

    assert raised.value.type == "RuntimeError"
    _assert_safe(str(raised.value))
    _assert_safe(_serialized_failure(raised.value))


def test_preflight_failure_scrubs_operator_variants_without_run_map() -> None:
    register_secret_value(OPERATOR_SECRET)
    effects.configure(
        effects.WorkerContext(
            mcp_transport=_FailingPreflightTransport(OPERATOR_ECHO)
        )
    )

    with pytest.raises(ApplicationError) as raised:
        asyncio.run(
            harness.preflightMcp(
                {
                    "workflowId": "operator-preflight",
                    "manifestJson": _mcp_manifest(),
                    "policy": "pin",
                }
            )
        )

    _assert_variants_safe(str(raised.value), OPERATOR_VARIANTS)
    _assert_variants_safe(_serialized_failure(raised.value), OPERATOR_VARIANTS)


def _pure_secret_failure(_value: Any) -> Any:
    raise RuntimeError(f"pure echoed {ECHO}")


register_pure("secret_failure_scrub.pure", _pure_secret_failure)


def test_workflow_rethrow_and_live_projection_scrub_secret_variants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_execute_activity(*_args: Any, **_kwargs: Any) -> Any:
        return None

    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)
    workflow = FlowWorkflow()
    inp = FlowInput(
        session_id="secret-projection",
        input={"safe": True},
        flow_json=arr("secret_failure_scrub.pure").to_json(),
        manifest_json={},
        max_call_limits={},
        secrets={"tenant-token": SECRET},
        mcp_preflight={"policy": "off", "completed": True},
    )

    with pytest.raises(ApplicationError) as raised:
        asyncio.run(workflow.run(inp))

    assert raised.value.type == "RuntimeError"
    assert raised.value.__suppress_context__ is True
    _assert_safe(str(raised.value))
    _assert_safe(_serialized_failure(raised.value))
    projection = workflow.projection()
    failed = [event for event in projection["events"] if event["type"] == "Failed"]
    assert failed
    _assert_safe(json.dumps(failed, sort_keys=True))
    assert all("[REDACTED]" in event["error"] for event in failed)


def test_structural_trajectory_failure_attrs_scrub_secret_variants() -> None:
    sink = InMemoryTrajectoryStore()
    effects.configure(
        effects.WorkerContext(
            trajectory_sink=sink,
            trajectory_blob_store=InMemoryBlobStore(),
        )
    )
    asyncio.run(
        harness.flushStructural(
            {
                "runId": "secret-trajectory",
                "rootRunId": "secret-trajectory",
                "segmentSeq": 0,
                "nodeOps": {"node": "seq"},
                "secrets": {"tenant-token": SECRET},
                "events": [
                    {
                        "eventId": "failure",
                        "type": "Failed",
                        "node": "node",
                        "cid": "cid",
                        "ts": 1.0,
                        "error": f"failure: {ECHO}",
                        "attrs": {"diagnostic": ECHO},
                    }
                ],
            }
        )
    )

    [step] = sink.list_trajectory_steps("secret-trajectory")
    _assert_safe(step)
    assert step.error.count("[REDACTED]") == 3
    assert step.attrs["diagnostic"].count("[REDACTED]") == 3
