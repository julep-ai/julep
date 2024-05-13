from temporalio.client import Client, TLSConfig
from uuid import UUID
from agents_api.env import (
    temporal_worker_url,
    temporal_namespace,
    temporal_client_cert,
    temporal_private_key,
)


async def get_client():
    tls_config = False

    if temporal_private_key and temporal_client_cert:
        tls_config = TLSConfig(
            client_cert=temporal_client_cert.encode(),
            client_private_key=temporal_private_key.encode(),
        )

    return await Client.connect(
        temporal_worker_url,
        namespace=temporal_namespace,
        tls=tls_config,
    )


async def run_summarization_task(session_id: UUID, job_id: UUID):
    client = await get_client()

    await client.execute_workflow(
        "SummarizationWorkflow",
        args=[str(session_id)],
        task_queue="memory-task-queue",
        id=str(job_id),
    )


async def run_embed_docs_task(
    doc_id: UUID, title: str, content: list[str], job_id: UUID
):
    client = await get_client()

    await client.execute_workflow(
        "EmbedDocsWorkflow",
        args=[str(doc_id), title, content],
        task_queue="memory-task-queue",
        id=str(job_id),
    )
