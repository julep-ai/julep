from datetime import timedelta
from uuid import UUID

from temporalio.client import Client, TLSConfig

from ..autogen.openapi_model import TransitionTarget
from ..common.protocol.tasks import ExecutionInput
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


async def run_task_execution_workflow(
    *,
    execution_input: ExecutionInput,
    job_id: UUID,
    start: TransitionTarget = TransitionTarget(workflow="main", step=0),
    previous_inputs: list[dict] = [],
    client: Client | None = None,
):
    from ..workflows.task_execution import TaskExecutionWorkflow

    client = client or (await get_client())

    return await client.start_workflow(
        TaskExecutionWorkflow.run,
        args=[execution_input, start, previous_inputs],
        task_queue=temporal_task_queue,
        id=str(job_id),
        run_timeout=timedelta(days=31),
        # TODO: Should add search_attributes for queryability
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


async def run_truncation_task(
    token_count_threshold: int, developer_id: UUID, session_id: UUID, job_id: UUID
):
    client = await get_client()

    await client.execute_workflow(
        "TruncationWorkflow",
        args=[str(developer_id), str(session_id), token_count_threshold],
        task_queue="memory-task-queue",
        id=str(job_id),
    )


async def run_summarization_task(session_id: UUID, job_id: UUID):
    client = await get_client()

    await client.execute_workflow(
        "SummarizationWorkflow",
        args=[str(session_id)],
        task_queue="memory-task-queue",
        id=str(job_id),
    )
