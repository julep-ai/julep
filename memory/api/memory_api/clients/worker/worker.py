import httpx
from memory_api.env import worker_url
from .types import MemoryManagementTaskArgs, MemoryManagementTask


async def add_summarization_task(data: MemoryManagementTaskArgs):
    with httpx.AsyncClient(timeout=30) as client:
        data = MemoryManagementTask(
            name="memory_management.v1",
            args=data,
        )
        await client.post(
            worker_url,
            headers={"Content-Type": "json"},
            json=data.model_dump_json(),
        )
