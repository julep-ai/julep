"""Small Temporal gateway used by the HTTP control plane.

The Temporal SDK is imported only by the async factory or individual methods,
keeping discovery of the optional server package lightweight.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Protocol

if TYPE_CHECKING:
    from ..app_deploy import PipelineRelease
    from .settings import ServerSettings


class TemporalStartAmbiguous(Exception):
    """The Temporal start request may have been accepted by the service."""


class TemporalGateway(Protocol):
    """The Temporal operations needed by routes and the run reconciler."""

    async def start_flow(
        self,
        pipeline: PipelineRelease,
        *,
        workflow_id: str,
        run_id: str,
        input: Any,
        principal: dict[str, Any],
        queue_lanes: Optional[dict[str, str]],
        secrets: Optional[dict[str, str]],
    ) -> str: ...

    async def cancel(self, workflow_id: str) -> None: ...

    async def terminate(self, workflow_id: str) -> None: ...

    async def describe(self, workflow_id: str) -> str: ...

    async def signal(self, workflow_id: str, name: str, arg: Any) -> None: ...

    async def query(self, workflow_id: str, name: str) -> Any: ...


class TemporalClientGateway:
    """A :class:`TemporalGateway` backed by a Temporal SDK client."""

    def __init__(self, client: Any, settings: ServerSettings) -> None:
        self._client = client
        self._settings = settings

    @property
    def client(self) -> Any:
        """Expose the SDK client for diagnostics without widening route usage."""

        return self._client

    async def start_flow(
        self,
        pipeline: PipelineRelease,
        *,
        workflow_id: str,
        run_id: str,
        input: Any,
        principal: dict[str, Any],
        queue_lanes: Optional[dict[str, str]],
        secrets: Optional[dict[str, str]],
    ) -> str:
        """Start one release-pinned flow with projection egress enabled."""

        from ..deploy import WorkflowStartOptions
        from ..execution.harness import start_flow

        if pipeline.task_queue is None:
            raise ValueError("the release pipeline has no pinned Temporal task queue")
        options = WorkflowStartOptions(
            workflow_id_reuse_policy="reject_duplicate",
            workflow_id_conflict_policy="fail",
            require_payload_encryption=self._settings.payload_encryption_required,
        )
        if options.require_payload_encryption:
            from ..execution.codec import data_converter_uses_aes_gcm

            config_method = getattr(self._client, "config", None)
            if not callable(config_method):
                raise ValueError(
                    "payload encryption requires a verifiable Temporal client with config()"
                )
            config = config_method(active_config=True)
            converter = config.get("data_converter") if isinstance(config, dict) else None
            if not data_converter_uses_aes_gcm(converter):
                raise ValueError(
                    "Temporal starts require the AES-256-GCM data converter; "
                    "configure TEMPORAL_PAYLOAD_KEYS and TEMPORAL_PAYLOAD_KEY_ID"
                )

        try:
            handle = await start_flow(
                self._client,
                pipeline.flow_json,
                pipeline.manifest_json,
                session_id=workflow_id,
                input=input,
                task_queue=pipeline.task_queue,
                policy=pipeline.execution_policy,
                pinned_pures=pipeline.pinned_pures,
                max_call_limits=dict(pipeline.max_call_limits),
                principal=principal,
                secrets=secrets,
                mcp_preflight=(
                    None
                    if pipeline.mcp_preflight_policy is None
                    else {
                        "policy": pipeline.mcp_preflight_policy,
                        "completed": False,
                        "surfaceDigest": None,
                    }
                ),
                bundle=pipeline.bundle_ref,
                runtime_declarations_ref=pipeline.runtime_declarations_ref,
                queue_lanes=queue_lanes,
                workflow_start_options=options.temporal_kwargs(),
                run_id=run_id,
                emit_projection=True,
                projection_batch_size=self._settings.projection_batch_size,
                projection_batch_interval_s=self._settings.projection_batch_interval_s,
            )
            temporal_run_id = getattr(handle, "result_run_id", None) or getattr(
                handle, "run_id", None
            )
            if not isinstance(temporal_run_id, str) or not temporal_run_id:
                raise RuntimeError(
                    "Temporal did not return a run ID for the started workflow"
                )
        except Exception as exc:
            raise TemporalStartAmbiguous(
                f"Temporal workflow start outcome is unknown: {type(exc).__name__}"
            ) from exc
        return temporal_run_id

    async def cancel(self, workflow_id: str) -> None:
        handle = self._client.get_workflow_handle(workflow_id)
        await handle.cancel()

    async def terminate(self, workflow_id: str) -> None:
        handle = self._client.get_workflow_handle(workflow_id)
        await handle.terminate(reason="terminated via Julep API")

    async def describe(self, workflow_id: str) -> str:
        from temporalio.service import RPCError, RPCStatusCode

        handle = self._client.get_workflow_handle(workflow_id)
        try:
            description = await handle.describe()
        except RPCError as exc:
            if exc.status is RPCStatusCode.NOT_FOUND:
                return "not_found"
            raise
        status = description.status
        return "unknown" if status is None else str(status.name).lower()

    async def signal(self, workflow_id: str, name: str, arg: Any) -> None:
        handle = self._client.get_workflow_handle(workflow_id)
        await handle.signal(name, arg)

    async def query(self, workflow_id: str, name: str) -> Any:
        handle = self._client.get_workflow_handle(workflow_id)
        return await handle.query(name)


async def create_temporal_gateway(settings: ServerSettings) -> TemporalClientGateway:
    """Connect a gateway with the same TLS/encryption contract as workers."""

    try:
        from temporalio.client import Client
    except ImportError as exc:
        raise RuntimeError(
            "the API server requires temporalio; install 'julep[server]'"
        ) from exc

    connect_kwargs: dict[str, Any] = {
        "namespace": settings.temporal_namespace,
        # Always explicit: the SDK otherwise turns TLS on implicitly when an
        # API key is supplied, overriding an explicit TEMPORAL_TLS=false.
        "tls": settings.temporal_tls,
    }
    if settings.temporal_api_key is not None:
        connect_kwargs["api_key"] = settings.temporal_api_key
    if settings.payload_keys is not None:
        from temporalio.common import HeaderCodecBehavior

        from ..execution.codec import parse_aes_gcm_keyring
        from ..execution.trace_headers import WorkflowTraceHeadersInterceptor
        from ..execution.worker import encrypted_payload_converter

        if settings.payload_key_id is None:
            raise ValueError(
                "TEMPORAL_PAYLOAD_KEY_ID is required when TEMPORAL_PAYLOAD_KEYS is set"
            )
        connect_kwargs["data_converter"] = encrypted_payload_converter(
            parse_aes_gcm_keyring(settings.payload_keys),
            active_key_id=settings.payload_key_id,
        )
        connect_kwargs["header_codec_behavior"] = HeaderCodecBehavior.CODEC
        connect_kwargs["interceptors"] = [WorkflowTraceHeadersInterceptor()]
    elif settings.payload_encryption_required:
        raise ValueError(
            "Temporal payload encryption is required but payload keys are not configured"
        )

    client = await Client.connect(settings.temporal_address, **connect_kwargs)
    return TemporalClientGateway(client, settings)


__all__ = [
    "TemporalClientGateway",
    "TemporalGateway",
    "TemporalStartAmbiguous",
    "create_temporal_gateway",
]
