import httpx

from agents_api.env import worker_url

from .types import (
    MemoryManagementTask,
    MemoryManagementTaskArgs,
)


async def add_summarization_task(data: MemoryManagementTaskArgs):
    async with httpx.AsyncClient(timeout=30) as client:
        data = MemoryManagementTask(
            name="memory_management.v1",
            args=data,
        )

        await client.post(
            f"{worker_url}/task",
            headers={"Content-Type": "json"},
            data=data.model_dump_json(),
        )
