from uuid import UUID

from temporalio.client import Client, TLSConfig

from agents_api.env import (
    temporal_client_cert,
    temporal_namespace,
    temporal_private_key,
    temporal_worker_url,
)

from ..common.protocol.tasks import ExecutionInput
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


async def run_summarization_task(
    session_id: UUID, job_id: UUID, client: Client | None = None
):
    client = client or (await get_client())

    await client.execute_workflow(
        "SummarizationWorkflow",
        args=[str(session_id)],
        task_queue="memory-task-queue",
        id=str(job_id),
    )


async def run_embed_docs_task(
    doc_id: UUID,
    title: str,
    content: list[str],
    job_id: UUID,
    client: Client | None = None,
):
    client = client or (await get_client())

    await client.execute_workflow(
        "EmbedDocsWorkflow",
        args=[str(doc_id), title, content],
        task_queue="memory-task-queue",
        id=str(job_id),
    )


async def run_truncation_task(
    token_count_threshold: int,
    session_id: UUID,
    job_id: UUID,
    client: Client | None = None,
):
    client = client or (await get_client())

    await client.execute_workflow(
        "TruncationWorkflow",
        args=[str(session_id), token_count_threshold],
        task_queue="memory-task-queue",
        id=str(job_id),
    )


async def run_task_execution_workflow(
    execution_input: ExecutionInput,
    job_id: UUID,
    start: tuple[str, int] = ("main", 0),
    previous_inputs: list[dict] = [],
    client: Client | None = None,
):
    client = client or (await get_client())

    return await client.start_workflow(
        "TaskExecutionWorkflow",
        args=[execution_input, start, previous_inputs],
        task_queue="memory-task-queue",
        id=str(job_id),
    )
