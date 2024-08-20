import asyncio
import logging
from contextlib import asynccontextmanager
from unittest.mock import patch

from fastapi.testclient import TestClient
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
    async with await WorkflowEnvironment.start_time_skipping(
        data_converter=pydantic_data_converter
    ) as env:
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


@asynccontextmanager
async def patch_http_client_with_temporal(*, cozo_client, developer_id):
    async with patch_testing_temporal():
        from agents_api.env import api_key, api_key_header_name
        from agents_api.web import app

        client = TestClient(app=app)
        app.state.cozo_client = cozo_client

        def make_request(method, url, **kwargs):
            headers = kwargs.pop("headers", {})
            headers = {
                **headers,
                "X-Developer-Id": str(developer_id),
                api_key_header_name: api_key,
            }

            return client.request(method, url, headers=headers, **kwargs)

        yield make_request, client
