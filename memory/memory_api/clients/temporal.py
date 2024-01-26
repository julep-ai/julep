from temporalio.client import Client
from uuid import UUID, uuid4
from memory_api.env import temporal_worker_url


async def run_summarization_task(session_id: UUID):
    client = await Client.connect(temporal_worker_url)
    await client.execute_workflow(
        "SummarizationWorkflow",
        args=[session_id],
        task_queue="memory-task-queue",
        id=str(uuid4()),
    )
