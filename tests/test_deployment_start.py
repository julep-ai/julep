from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any

import pytest

pytest.importorskip("temporalio")

from julep import WorkflowStartOptions, deploy, ident
from julep.freeze import McpSnapshot


class _FakeClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def start_workflow(self, workflow: Any, arg: Any, **kwargs: Any) -> str:
        from julep.execution.trace_headers import current_workflow_trace_headers

        self.calls.append({"workflow": workflow, "arg": arg, "kwargs": kwargs})
        self.trace_headers = current_workflow_trace_headers()
        return "handle"


def test_deployment_start_is_non_blocking_and_forwards_explicit_options() -> None:
    deployment = deploy(ident(), McpSnapshot(), queue="summary")
    client = _FakeClient()
    options = WorkflowStartOptions(
        execution_timeout=timedelta(minutes=5),
        search_attributes={"StoreId": "store-1"},
        trace_headers={"traceparent": "00-abc"},
        task_queue="memory-summary",
        require_payload_encryption=False,
    )
    from temporalio.common import HeaderCodecBehavior
    from julep.execution.trace_headers import WorkflowTraceHeadersInterceptor

    client.config = lambda **_kwargs: {
        "interceptors": [WorkflowTraceHeadersInterceptor()],
        "header_codec_behavior": HeaderCodecBehavior.CODEC,
    }

    result = asyncio.run(
        deployment.start(
            client,
            session_id="mem:episode-summary:s:e:g1",
            input={"generation": 1},
            options=options,
        )
    )

    assert result == "handle"
    (call,) = client.calls
    kwargs = call["kwargs"]
    assert kwargs["id"] == "mem:episode-summary:s:e:g1"
    assert kwargs["task_queue"] == "memory-summary"
    assert kwargs["execution_timeout"] == timedelta(minutes=5)
    assert kwargs["search_attributes"] == {"StoreId": ["store-1"]}
    assert "rpc_metadata" not in kwargs
    assert client.trace_headers == {"traceparent": "00-abc"}
    assert kwargs["id_reuse_policy"].name == "ALLOW_DUPLICATE_FAILED_ONLY"
    assert kwargs["id_conflict_policy"].name == "USE_EXISTING"


def test_start_options_validate_policies_and_timeout() -> None:
    with pytest.raises(ValueError, match="reuse_policy"):
        WorkflowStartOptions(workflow_id_reuse_policy="always")
    with pytest.raises(ValueError, match="positive"):
        WorkflowStartOptions(execution_timeout=timedelta(0))


def test_start_options_normalize_scalar_search_attributes_for_temporal() -> None:
    from temporalio.api.common.v1 import SearchAttributes
    from temporalio.converter import encode_search_attributes

    attributes = WorkflowStartOptions(
        search_attributes={"StoreId": "store-1", "Generation": 7}
    ).temporal_kwargs()["search_attributes"]
    encoded = SearchAttributes()

    encode_search_attributes(attributes, encoded)

    assert set(encoded.indexed_fields) == {"StoreId", "Generation"}


def test_start_options_default_to_encryption_required() -> None:
    assert WorkflowStartOptions().require_payload_encryption is True


def test_duplicate_successful_start_returns_existing_handle() -> None:
    from temporalio.exceptions import WorkflowAlreadyStartedError

    class DuplicateClient(_FakeClient):
        async def start_workflow(self, workflow: Any, arg: Any, **kwargs: Any) -> str:
            raise WorkflowAlreadyStartedError(kwargs["id"], "FlowWorkflow")

        def get_workflow_handle(self, workflow_id: str) -> str:
            return f"existing:{workflow_id}"

    deployment = deploy(ident(), McpSnapshot(), queue="summary")
    result = asyncio.run(
        deployment.start(
            DuplicateClient(),
            session_id="mem:episode-summary:s:e:g1",
            input={},
            options=WorkflowStartOptions(require_payload_encryption=False),
        )
    )

    assert result == "existing:mem:episode-summary:s:e:g1"


def test_explicit_reject_duplicate_policy_is_honored() -> None:
    from temporalio.exceptions import WorkflowAlreadyStartedError

    class DuplicateClient(_FakeClient):
        async def start_workflow(self, workflow: Any, arg: Any, **kwargs: Any) -> str:
            raise WorkflowAlreadyStartedError(kwargs["id"], "FlowWorkflow")

        def get_workflow_handle(self, workflow_id: str) -> str:
            return f"existing:{workflow_id}"

    deployment = deploy(ident(), McpSnapshot(), queue="summary")
    with pytest.raises(WorkflowAlreadyStartedError):
        asyncio.run(
            deployment.start(
                DuplicateClient(),
                session_id="mem:episode-summary:s:e:g1",
                input={},
                options=WorkflowStartOptions(
                    workflow_id_reuse_policy="reject_duplicate",
                    require_payload_encryption=False,
                ),
            )
        )


def test_trace_headers_reject_client_without_header_codec() -> None:
    from julep.execution.trace_headers import WorkflowTraceHeadersInterceptor

    client = _FakeClient()
    client.config = lambda **_kwargs: {
        "interceptors": [WorkflowTraceHeadersInterceptor()],
    }
    deployment = deploy(ident(), McpSnapshot(), queue="summary")

    with pytest.raises(ValueError, match="HeaderCodecBehavior.CODEC"):
        asyncio.run(
            deployment.start(
                client,
                session_id="mem:episode-summary:s:e:g1",
                input={},
                options=WorkflowStartOptions(
                    trace_headers={"traceparent": "00-abc"},
                    require_payload_encryption=False,
                ),
            )
        )
