import asyncio
import io
import logging
from contextlib import asynccontextmanager, contextmanager
from unittest.mock import patch

from botocore import exceptions
from fastapi.testclient import TestClient
from litellm.types.utils import ModelResponse
from temporalio.testing import WorkflowEnvironment

from agents_api.worker.codec import pydantic_data_converter
from agents_api.worker.worker import create_worker

# Replicated here to prevent circular import
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
    async with patch_testing_temporal() as (worker, mock_get_client):
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

        temporal_client = await mock_get_client()
        yield make_request, temporal_client


@contextmanager
def patch_embed_acompletion(output={"role": "assistant", "content": "Hello, world!"}):
    mock_model_response = ModelResponse(
        id="fake_id",
        choices=[
            dict(
                message=output,
                tool_calls=[],
                created_at=1,
                # finish_reason="stop",
            )
        ],
        created=0,
        object="text_completion",
    )

    with patch("agents_api.clients.litellm.aembedding") as embed, patch(
        "agents_api.clients.litellm.acompletion"
    ) as acompletion:
        embed.return_value = [[1.0] * EMBEDDING_SIZE]
        acompletion.return_value = mock_model_response

        yield embed, acompletion


@contextmanager
def patch_integration_service(output: dict = {"result": "ok"}):
    with patch(
        "agents_api.clients.integrations.run_integration_service"
    ) as run_integration_service:
        run_integration_service.return_value = output

        yield run_integration_service


@contextmanager
def patch_s3_client():
    class InMemoryS3Client:
        def __init__(self):
            self.store = {}

        def list_buckets(self):
            return {"Buckets": [{"Name": bucket} for bucket in self.store.keys()]}

        def create_bucket(self, Bucket):
            self.store[Bucket] = {}

        def head_object(self, Bucket, Key):
            obj = self.store.get(Bucket, {}).get(Key)

            if obj is None:
                raise exceptions.ClientError(
                    {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
                )

            return obj

        def put_object(self, Bucket, Key, Body):
            self.store[Bucket] = self.store.get(Bucket, {})
            self.store[Bucket][Key] = Body

        def get_object(self, Bucket, Key):
            obj = self.store.get(Bucket, {}).get(Key)

            if obj is None:
                raise exceptions.ClientError(
                    {"Error": {"Code": "404", "Message": "Not Found"}}, "GetObject"
                )

            file_io = io.BytesIO(obj)

            return {"Body": file_io}

        def delete_object(self, Bucket, Key):
            self.store[Bucket] = self.store.get(Bucket, {})
            del self.store[Bucket][Key]

    in_memory_s3_client = InMemoryS3Client()

    with patch("agents_api.clients.s3.get_s3_client") as get_s3_client:
        get_s3_client.return_value = in_memory_s3_client

        yield get_s3_client
