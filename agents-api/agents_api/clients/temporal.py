from datetime import timedelta
from uuid import UUID

from beartype import beartype
from temporalio.client import Client, TLSConfig
from temporalio.common import (
    SearchAttributeKey,
    SearchAttributePair,
    TypedSearchAttributes,
)

from ..autogen.openapi_model import TransitionTarget
from ..common.protocol.tasks import ExecutionInput
from ..common.retry_policies import DEFAULT_RETRY_POLICY
from ..common.storage_handler import store_in_blob_store_if_large
from ..env import (
    temporal_client_cert,
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

    if temporal_private_key and temporal_client_cert:
        tls_config = TLSConfig(
            client_cert=temporal_client_cert.encode(),
            client_private_key=temporal_private_key.encode(),
        )

    return await Client.connect(
        worker_url,
        namespace=namespace,
        tls=tls_config,
        data_converter=data_converter,
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

    start: TransitionTarget = start or TransitionTarget(workflow="main", step=0)
    previous_inputs: list[dict] = previous_inputs or []

    client = client or (await get_client())
    execution_id = execution_input.execution.id
    execution_id_key = SearchAttributeKey.for_keyword("CustomStringField")
    execution_input.arguments = store_in_blob_store_if_large(execution_input.arguments)

    return await client.start_workflow(
        TaskExecutionWorkflow.run,
        args=[execution_input, start, previous_inputs],
        task_queue=temporal_task_queue,
        id=str(job_id),
        run_timeout=timedelta(days=31),
        retry_policy=DEFAULT_RETRY_POLICY,
        search_attributes=TypedSearchAttributes(
            [
                SearchAttributePair(execution_id_key, str(execution_id)),
            ]
        ),
    )


async def get_workflow_handle(
    *,
    handle_id: str,
    client: Client | None = None,
):
    client = client or (await get_client())

    handle = client.get_workflow_handle(
        handle_id,
    )

    return handle
