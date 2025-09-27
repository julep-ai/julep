"""
This script initializes and runs a Temporal worker that listens for tasks on a specified queue.
It supports various workflows and activities related to agents' operations.
"""

# !/usr/bin/env python3

import asyncio
import logging

from tenacity import after_log, retry, retry_if_exception_type, wait_fixed

from ..app import app, lifespan
from ..clients import temporal
from .worker import create_worker

logger = logging.getLogger(__name__)
h = logging.StreamHandler()
fmt = logging.Formatter("[%(asctime)s/%(levelname)s] - %(message)s")
h.setFormatter(fmt)
logger.addHandler(h)
logger.setLevel(logging.DEBUG)


@retry(
    wait=wait_fixed(20),
    retry=retry_if_exception_type(RuntimeError),
    after=after_log(logger, logging.DEBUG),
)
async def main() -> None:
    """
    Initializes the Temporal client and worker with TLS configuration (if provided),
    then starts the worker to listen for tasks on the configured task queue.
    """

    client = await temporal.get_client_with_metrics()
    worker = create_worker(client)
    if hasattr(worker, "_workflow_worker") and worker._workflow_worker:  # noqa: SLF001
        worker._workflow_worker._deadlock_timeout_seconds = 60  # noqa: SLF001

    async with lifespan(app):
        # Start the worker to listen for and process tasks
        await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
