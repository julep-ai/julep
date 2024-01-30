#!/usr/bin/env python3

import asyncio

from temporalio.client import Client, TLSConfig
from temporalio.worker import Worker

from ..activities.summarization import summarization
from ..env import (
    temporal_endpoint,
    temporal_task_queue,
    temporal_namespace,
    temporal_private_key,
    temporal_client_cert,
)
from ..workflows.summarization import SummarizationWorkflow


async def main():
    print(f"Starting worker on [{temporal_endpoint}]...")

    tls_config = False

    if temporal_private_key and temporal_client_cert:
        tls_config = TLSConfig(
            client_cert=temporal_client_cert.encode(),
            client_private_key=temporal_private_key.encode(),
        )

    client = await Client.connect(
        temporal_endpoint,
        namespace=temporal_namespace,
        tls=tls_config,
    )

    print(f"Queue: {temporal_task_queue}")
    worker = Worker(
        client,
        task_queue=temporal_task_queue,
        workflows=[SummarizationWorkflow],
        activities=[summarization],
    )

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
