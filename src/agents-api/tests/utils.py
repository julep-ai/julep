import asyncio
import logging
import math
import os
import subprocess
from contextlib import asynccontextmanager, contextmanager
from typing import Any
from unittest.mock import patch
from uuid import UUID

from agents_api.autogen.openapi_model import Transition
from agents_api.common.protocol.tasks import TransitionTarget, TransitionType
from agents_api.common.utils.datetime import utcnow
from agents_api.worker.codec import pydantic_data_converter
from agents_api.worker.worker import create_worker
from fastapi.testclient import TestClient
from litellm.types.utils import ModelResponse
from temporalio.testing import WorkflowEnvironment
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.localstack import LocalStackContainer
from testcontainers.postgres import PostgresContainer
from uuid_extensions import uuid7

# Replicated here to prevent circular import
EMBEDDING_SIZE: int = 1024


def make_vector_with_similarity(n: int = EMBEDDING_SIZE, d: float = 0.5):
    """
    Returns a list `v` of length `n` such that the cosine similarity
    between `v` and the all-ones vector of length `n` is approximately d.
    """
    if not -1.0 <= d <= 1.0:
        msg = "d must lie in [-1, 1]."
        raise ValueError(msg)

    # Handle special cases exactly:
    if abs(d - 1.0) < 1e-12:  # d ~ +1
        return [1.0] * n
    if abs(d + 1.0) < 1e-12:  # d ~ -1
        return [-1.0] * n
    if abs(d) < 1e-12:  # d ~ 0
        v = [0.0] * n
        if n >= 2:
            v[0] = 1.0
            v[1] = -1.0
        return v

    sign_d = 1.0 if d >= 0 else -1.0

    # Base part: sign(d)*[1,1,...,1]
    base = [sign_d] * n

    # Orthogonal unit vector u with sum(u)=0; for simplicity:
    #   u = [1/sqrt(2), -1/sqrt(2), 0, 0, ..., 0]
    u = [0.0] * n
    if n >= 2:
        u[0] = 1.0 / math.sqrt(2)
        u[1] = -1.0 / math.sqrt(2)
    # (if n=1, there's no truly orthogonal vector to [1], so skip)

    # Solve for alpha:
    # alpha^2 = n*(1 - d^2)/d^2
    alpha = math.sqrt(n * (1 - d * d)) / abs(d)

    # Construct v
    v = [0.0] * n
    for i in range(n):
        v[i] = base[i] + alpha * u[i]

    return v


def generate_transition(
    execution_id: UUID = uuid7(),
    transition_id: UUID = uuid7(),
    type: TransitionType = "step",
    current_step: TransitionTarget = TransitionTarget(
        workflow="main",
        step=0,
        scope_id=uuid7(),
    ),
    next_step: TransitionTarget | None = None,
    task_token: str | None = None,
    output: Any = None,
    label: str | None = None,
    metadata: dict = {},
):
    return Transition(
        execution_id=execution_id,
        id=transition_id,
        type=type,
        current=current_step,
        next=next_step,
        task_token=task_token,
        output=output,
        label=label,
        created_at=utcnow(),
        updated_at=utcnow(),
        metadata=metadata,
    )


@asynccontextmanager
async def patch_testing_temporal():
    # Set log level to ERROR to avoid spamming the console
    logger = logging.getLogger("temporalio")
    previous_log_level = logger.getEffectiveLevel()

    logger.setLevel(logging.ERROR)

    # Start a local Temporal environment
    async with await WorkflowEnvironment.start_time_skipping(
        data_converter=pydantic_data_converter,
    ) as env:
        # Create a worker with our workflows and start it
        worker = create_worker(client=env.client)
        env.worker_task = asyncio.create_task(worker.run())

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
async def patch_http_client_with_temporal(*, postgres_pool, developer_id):
    async with patch_testing_temporal() as (_worker, mock_get_client):
        from agents_api.env import api_key, api_key_header_name
        from agents_api.web import app

        client = TestClient(app=app)
        app.state.postgres_pool = postgres_pool

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
            {
                "message": output,
                "tool_calls": [],
                "created_at": 1,
                "finish_reason": "stop",
            },
        ],
        created=0,
        object="text_completion",
        usage={"total_tokens": 10, "prompt_tokens": 5, "completion_tokens": 5},
    )

    with (
        patch("agents_api.clients.litellm.aembedding") as embed,
        patch("agents_api.clients.litellm.acompletion") as acompletion,
    ):
        embed.return_value = [[1.0] * EMBEDDING_SIZE]
        acompletion.return_value = mock_model_response

        yield embed, acompletion


@contextmanager
def patch_integration_service(output: dict = {"result": "ok"}):
    with patch(
        "agents_api.clients.integrations.run_integration_service",
    ) as run_integration_service:
        run_integration_service.return_value = output

        yield run_integration_service


@contextmanager
def get_pg_dsn(start_vectorizer: bool = False):
    with PostgresContainer("timescale/timescaledb-ha:pg17-ts2.18-all") as postgres:
        test_psql_url = postgres.get_connection_url()
        pg_dsn = f"postgres://{test_psql_url[22:]}?sslmode=disable"
        command = f"migrate -database '{pg_dsn}' -path ../memory-store/migrations/ up"
        process = subprocess.Popen(command, shell=True)
        process.wait()

        if not start_vectorizer:
            yield pg_dsn
            return

        # ELSE:
        with (
            DockerContainer("timescale/pgai-vectorizer-worker:latest")
            .with_network(postgres._network)  # noqa: SLF001
            .with_env(
                "PGAI_VECTORIZER_WORKER_DB_URL",
                pg_dsn.replace("localhost", postgres.get_container_host_ip()),
            )
            .with_env(
                "OPENAI_API_KEY",
                os.environ.get("OPENAI_API_KEY"),
            )
        ) as vectorizer:
            wait_for_logs(
                vectorizer,
                "finished processing vectorizer",
                predicate_streams_and=True,
                raise_on_exit=True,
                timeout=10,
            )

        print("Vectorizer worker started")

        yield pg_dsn


@contextmanager
def get_localstack():
    with LocalStackContainer(image="localstack/localstack:s3-latest").with_services(
        "s3",
    ) as localstack:
        yield localstack
