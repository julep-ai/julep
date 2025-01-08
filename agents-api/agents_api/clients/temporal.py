from datetime import timedelta
from uuid import UUID

from beartype import beartype
from temporalio.client import Client, TLSConfig
from temporalio.common import (
    SearchAttributeKey,
    SearchAttributePair,
    TypedSearchAttributes,
)
from temporalio.contrib.opentelemetry import TracingInterceptor
from temporalio.runtime import PrometheusConfig, Runtime, TelemetryConfig

from ..autogen.openapi_model import TransitionTarget
from ..common.interceptors import offload_if_large
from ..common.protocol.tasks import ExecutionInput
from ..common.retry_policies import DEFAULT_RETRY_POLICY
from ..env import (
    temporal_api_key,
    temporal_client_cert,
    temporal_metrics_bind_host,
    temporal_metrics_bind_port,
    temporal_namespace,
    temporal_private_key,
    temporal_task_queue,
    temporal_worker_url,
)
from ..worker.codec import pydantic_data_converter


async def get_client(
    worker_url: str = temporal_worker_url,
    namespace: str = temporal_namespace,
    data_converter=pydantic_data_converter,
):
    tls_config = False
    rpc_metadata = {}

    if temporal_private_key and temporal_client_cert:
        tls_config = TLSConfig(
            client_cert=temporal_client_cert.encode(),
            client_private_key=temporal_private_key.encode(),
        )
    elif temporal_api_key:
        tls_config = True
        rpc_metadata = rpc_metadata = {"temporal-namespace": namespace}

    return await Client.connect(
        worker_url,
        namespace=namespace,
        tls=tls_config,
        data_converter=data_converter,
        api_key=temporal_api_key or None,
        rpc_metadata=rpc_metadata,
    )


async def get_client_with_metrics(
    worker_url: str = temporal_worker_url,
    namespace: str = temporal_namespace,
    data_converter=pydantic_data_converter,
):
    tls_config = False
    rpc_metadata = {}

    if temporal_private_key and temporal_client_cert:
        tls_config = TLSConfig(
            client_cert=temporal_client_cert.encode(),
            client_private_key=temporal_private_key.encode(),
        )
    elif temporal_api_key:
        tls_config = True
        rpc_metadata = rpc_metadata = {"temporal-namespace": namespace}

    new_runtime = Runtime(
        telemetry=TelemetryConfig(
            metrics=PrometheusConfig(
                bind_address=f"{temporal_metrics_bind_host}:{temporal_metrics_bind_port}"
            ),
        ),
    )

    return await Client.connect(
        worker_url,
        namespace=namespace,
        tls=tls_config,
        data_converter=data_converter,
        runtime=new_runtime,
        interceptors=[TracingInterceptor()],
        api_key=temporal_api_key or None,
        rpc_metadata=rpc_metadata,
    )


@beartype
async def run_task_execution_workflow(
    *,
    execution_input: ExecutionInput,
    job_id: UUID,
    start: TransitionTarget | None = None,
    previous_inputs: list[dict] | None = None,
    client: Client | None = None,
):
    from ..workflows.task_execution import TaskExecutionWorkflow

    if execution_input.execution is None:
        msg = "execution_input.execution cannot be None"
        raise ValueError(msg)

    start: TransitionTarget = start or TransitionTarget(workflow="main", step=0)

    client = client or (await get_client())
    execution_id = execution_input.execution.id
    execution_id_key = SearchAttributeKey.for_keyword("CustomStringField")

    old_args = execution_input.arguments
    execution_input.arguments = await offload_if_large(old_args)

    previous_inputs: list[dict] = previous_inputs or [execution_input.arguments]

    return await client.start_workflow(
        TaskExecutionWorkflow.run,
        args=[execution_input, start, previous_inputs],
        task_queue=temporal_task_queue,
        id=str(job_id),
        run_timeout=timedelta(days=31),
        retry_policy=DEFAULT_RETRY_POLICY,
        search_attributes=TypedSearchAttributes([
            SearchAttributePair(execution_id_key, str(execution_id)),
        ]),
    )


async def get_workflow_handle(
    *,
    handle_id: str,
    client: Client | None = None,
):
    client = client or (await get_client())

    return client.get_workflow_handle(
        handle_id,
    )
