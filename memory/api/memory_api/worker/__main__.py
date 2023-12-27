#!/usr/bin/env python3

import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from ..activities.demo import say_hello
from ..env import temporal_endpoint, temporal_task_queue
from ..workflows.demo import GreetingWorkflow


async def main():
    print(f"Starting worker on [{temporal_endpoint}]...")
    client = await Client.connect(temporal_endpoint)

    print(f"Queue: {temporal_task_queue}")
    worker = Worker(
        client,
        task_queue=temporal_task_queue,
        workflows=[GreetingWorkflow],
        activities=[say_hello],
    )

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
