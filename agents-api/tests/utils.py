import asyncio
import logging
from contextlib import asynccontextmanager
from unittest.mock import patch

from temporalio.testing import WorkflowEnvironment

from agents_api.worker.codec import pydantic_data_converter
from agents_api.worker.worker import create_worker

EMBEDDING_SIZE: int = 1024


@asynccontextmanager
async def patch_testing_temporal():
    # Set log level to ERROR to avoid spamming the console
    logger = logging.getLogger("temporalio")
    previous_log_level = logger.getEffectiveLevel()

    logger.setLevel(logging.ERROR)

    # Start a local Temporal environment
    async with await WorkflowEnvironment.start_local() as env:
        # Set the correct codec
        env.client._config["data_converter"] = pydantic_data_converter

        # Create a worker with our workflows and start it
        worker = create_worker(client=env.client)
        asyncio.create_task(worker.run())

        # Mock the Temporal client
        mock_client = worker.client

        with patch("agents_api.clients.temporal.get_client") as mock_get_client:
            mock_get_client.return_value = mock_client

            # Yield the worker and the mock client <---
            yield worker, mock_get_client

        # Shutdown the worker
        await worker.shutdown()

    # Reset log level
    logger.setLevel(previous_log_level)
