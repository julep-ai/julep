from temporalio.client import Client, TLSConfig
from uuid import UUID, uuid4
from memory_api.env import (
    temporal_worker_url,
    temporal_namespace,
    temporal_client_cert,
    temporal_private_key,
)


async def run_summarization_task(session_id: UUID):
    tls_config = False

    if temporal_private_key and temporal_client_cert:
        tls_config = TLSConfig(
            client_cert=temporal_client_cert.encode(),
            client_private_key=temporal_private_key.encode(),
        )

    client = await Client.connect(
        temporal_worker_url,
        namespace=temporal_namespace,
        tls=tls_config,
    )
    await client.execute_workflow(
        "SummarizationWorkflow",
        args=[str(session_id)],
        task_queue="memory-task-queue",
        id=str(uuid4()),
    )
