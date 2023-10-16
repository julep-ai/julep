import httpx
from memory_api.env import worker_url
from .types import (
    MemoryManagementTaskArgs, 
    MemoryManagementTask,
    AddPrinciplesTask,
    AddPrinciplesTaskArgs,
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


async def add_principles_task(data: AddPrinciplesTaskArgs):
    async with httpx.AsyncClient(timeout=30) as client:
        data = AddPrinciplesTask(
            name="add_principles.v1",
            args=data,
        )

        await client.post(
            f"{worker_url}/task",
            headers={"Content-Type": "json"},
            data=data.model_dump_json(),
        )
