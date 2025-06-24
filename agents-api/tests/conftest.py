"""
Pytest configuration and fixtures for agents-api tests.
Migrated from Ward fixtures.py
"""

import contextlib
import os
import random
import string
from unittest.mock import patch
from uuid import UUID

import pytest
import pytest_asyncio
from agents_api.autogen.openapi_model import (
    CreateAgentRequest,
    CreateDocRequest,
    CreateExecutionRequest,
    CreateFileRequest,
    CreateProjectRequest,
    CreateSessionRequest,
    CreateTaskRequest,
    CreateToolRequest,
    CreateTransitionRequest,
    CreateUserRequest,
    PatchTaskRequest,
    UpdateTaskRequest,
)

# AIDEV-NOTE: Fix Pydantic forward reference issues
# Import all step types first
from agents_api.autogen.Tasks import (
    EvaluateStep,
    ForeachStep,
    IfElseWorkflowStep,
    ParallelStep,
    PromptStep,
    SwitchStep,
    ToolCallStep,
    WaitForInputStep,
    YieldStep,
)
from agents_api.clients.pg import create_db_pool
from agents_api.common.utils.memory import total_size
from agents_api.env import api_key, api_key_header_name, multi_tenant_mode
from agents_api.queries.agents.create_agent import create_agent
from agents_api.queries.developers.create_developer import create_developer
from agents_api.queries.developers.get_developer import get_developer
from agents_api.queries.docs.create_doc import create_doc
from agents_api.queries.docs.get_doc import get_doc
from agents_api.queries.executions.create_execution import create_execution
from agents_api.queries.executions.create_execution_transition import (
    create_execution_transition,
)
from agents_api.queries.executions.create_temporal_lookup import create_temporal_lookup
from agents_api.queries.files.create_file import create_file
from agents_api.queries.projects.create_project import create_project
from agents_api.queries.secrets.delete import delete_secret
from agents_api.queries.secrets.list import list_secrets
from agents_api.queries.sessions.create_session import create_session
from agents_api.queries.tasks.create_task import create_task
from agents_api.queries.tools.create_tools import create_tools
from agents_api.queries.users.create_user import create_user
from agents_api.web import app
from fastapi.testclient import TestClient
from temporalio.client import WorkflowHandle
from uuid_extensions import uuid7

from .utils import (
    get_pg_dsn,
    make_vector_with_similarity,
)
from .utils import (
    patch_embed_acompletion as patch_embed_acompletion_ctx,
)

# Rebuild models to resolve forward references
try:
    CreateTaskRequest.model_rebuild()
    CreateExecutionRequest.model_rebuild()
    PatchTaskRequest.model_rebuild()
    UpdateTaskRequest.model_rebuild()
    # Also rebuild any workflow step models that might have forward refs
    EvaluateStep.model_rebuild()
    ForeachStep.model_rebuild()
    IfElseWorkflowStep.model_rebuild()
    ParallelStep.model_rebuild()
    PromptStep.model_rebuild()
    SwitchStep.model_rebuild()
    ToolCallStep.model_rebuild()
    WaitForInputStep.model_rebuild()
    YieldStep.model_rebuild()
except Exception:
    pass  # Models might already be rebuilt

# Configure pytest-asyncio
pytest_asyncio.fixture_scope = "function"


# Session-scoped fixtures (equivalent to Ward's global scope)
@pytest.fixture(scope="session")
def pg_dsn():
    """PostgreSQL DSN for testing."""
    with get_pg_dsn() as dsn:
        os.environ["PG_DSN"] = dsn
        try:
            yield dsn
        finally:
            del os.environ["PG_DSN"]


@pytest.fixture(scope="session")
def test_developer_id():
    """Test developer ID."""
    if not multi_tenant_mode:
        return UUID(int=0)
    return uuid7()


@pytest.fixture
async def test_developer(pg_dsn, test_developer_id):
    """Test developer fixture."""
    pool = await create_db_pool(dsn=pg_dsn)
    return await get_developer(
        developer_id=test_developer_id,
        connection_pool=pool,
    )


# Function-scoped fixtures (equivalent to Ward's test scope)
@pytest.fixture
async def test_project(pg_dsn, test_developer):
    """Create a test project."""
    pool = await create_db_pool(dsn=pg_dsn)
    return await create_project(
        developer_id=test_developer.id,
        data=CreateProjectRequest(
            name="Test Project",
            metadata={"test": "test"},
        ),
        connection_pool=pool,
    )


@pytest.fixture
def patch_embed_acompletion():
    """Patch embed and acompletion functions."""
    output = {"role": "assistant", "content": "Hello, world!"}
    with patch_embed_acompletion_ctx(output) as (embed, acompletion):
        yield embed, acompletion


@pytest.fixture
async def test_agent(pg_dsn, test_developer, test_project):
    """Create a test agent."""
    pool = await create_db_pool(dsn=pg_dsn)
    return await create_agent(
        developer_id=test_developer.id,
        data=CreateAgentRequest(
            model="gpt-4o-mini",
            name="test agent",
            about="test agent about",
            metadata={"test": "test"},
            project=test_project.canonical_name,
        ),
        connection_pool=pool,
    )


@pytest.fixture
async def test_user(pg_dsn, test_developer):
    """Create a test user."""
    pool = await create_db_pool(dsn=pg_dsn)
    return await create_user(
        developer_id=test_developer.id,
        data=CreateUserRequest(
            name="test user",
            about="test user about",
        ),
        connection_pool=pool,
    )


@pytest.fixture
async def test_file(pg_dsn, test_developer, test_user):
    """Create a test file."""
    pool = await create_db_pool(dsn=pg_dsn)
    return await create_file(
        developer_id=test_developer.id,
        data=CreateFileRequest(
            name="Hello",
            description="World",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
        ),
        connection_pool=pool,
    )


@pytest.fixture
async def test_doc(pg_dsn, test_developer, test_agent):
    """Create a test document."""
    pool = await create_db_pool(dsn=pg_dsn)
    resp = await create_doc(
        developer_id=test_developer.id,
        data=CreateDocRequest(
            title="Hello",
            content=["World", "World2", "World3"],
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
    )

    # Explicitly Refresh Indices
    await pool.execute("REINDEX DATABASE")

    doc = await get_doc(developer_id=test_developer.id, doc_id=resp.id, connection_pool=pool)
    yield doc

    # TODO: Delete the doc
    # await delete_doc(
    #     developer_id=test_developer.id,
    #     doc_id=resp.id,
    #     owner_type="agent",
    #     owner_id=test_agent.id,
    #     connection_pool=pool,
    # )


@pytest.fixture
async def test_doc_with_embedding(pg_dsn, test_developer, test_doc):
    """Create a test document with embeddings."""
    pool = await create_db_pool(dsn=pg_dsn)
    embedding_with_confidence_0 = make_vector_with_similarity(d=0.0)
    embedding_with_confidence_0_5 = make_vector_with_similarity(d=0.5)
    embedding_with_confidence_neg_0_5 = make_vector_with_similarity(d=-0.5)
    embedding_with_confidence_1_neg = make_vector_with_similarity(d=-1.0)

    # Insert embedding with all 1.0s (similarity = 1.0)
    await pool.execute(
        """
        INSERT INTO docs_embeddings_store (developer_id, doc_id, index, chunk_seq, chunk, embedding)
        VALUES ($1, $2, 0, 0, $3, $4)
    """,
        test_developer.id,
        test_doc.id,
        test_doc.content[0] if isinstance(test_doc.content, list) else test_doc.content,
        f"[{', '.join([str(x) for x in [1.0] * 1024])}]",
    )

    # Insert embedding with confidence 0
    await pool.execute(
        """
        INSERT INTO docs_embeddings_store (developer_id, doc_id, index, chunk_seq, chunk, embedding)
        VALUES ($1, $2, 1, 1, $3, $4)
        """,
        test_developer.id,
        test_doc.id,
        "Test content 1",
        f"[{', '.join([str(x) for x in embedding_with_confidence_0])}]",
    )

    # Insert embedding with confidence 0.5
    await pool.execute(
        """
        INSERT INTO docs_embeddings_store (developer_id, doc_id, index, chunk_seq, chunk, embedding)
        VALUES ($1, $2, 2, 2, $3, $4)
        """,
        test_developer.id,
        test_doc.id,
        "Test content 2",
        f"[{', '.join([str(x) for x in embedding_with_confidence_0_5])}]",
    )

    # Insert embedding with confidence -0.5
    await pool.execute(
        """
        INSERT INTO docs_embeddings_store (developer_id, doc_id, index, chunk_seq, chunk, embedding)
        VALUES ($1, $2, 3, 3, $3, $4)
        """,
        test_developer.id,
        test_doc.id,
        "Test content 3",
        f"[{', '.join([str(x) for x in embedding_with_confidence_neg_0_5])}]",
    )

    # Insert embedding with confidence -1
    await pool.execute(
        """
        INSERT INTO docs_embeddings_store (developer_id, doc_id, index, chunk_seq, chunk, embedding)
        VALUES ($1, $2, 4, 4, $3, $4)
        """,
        test_developer.id,
        test_doc.id,
        "Test content 4",
        f"[{', '.join([str(x) for x in embedding_with_confidence_1_neg])}]",
    )

    # Explicitly Refresh Indices
    await pool.execute("REINDEX DATABASE")

    yield await get_doc(
        developer_id=test_developer.id, doc_id=test_doc.id, connection_pool=pool
    )


@pytest.fixture
async def test_user_doc(pg_dsn, test_developer, test_user):
    """Create a test document owned by a user."""
    pool = await create_db_pool(dsn=pg_dsn)
    resp = await create_doc(
        developer_id=test_developer.id,
        data=CreateDocRequest(
            title="Hello",
            content=["World", "World2", "World3"],
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    # Explicitly Refresh Indices
    await pool.execute("REINDEX DATABASE")

    doc = await get_doc(developer_id=test_developer.id, doc_id=resp.id, connection_pool=pool)
    yield doc

    # TODO: Delete the doc


@pytest.fixture
async def test_task(pg_dsn, test_developer, test_agent):
    """Create a test task."""
    pool = await create_db_pool(dsn=pg_dsn)
    return await create_task(
        developer_id=test_developer.id,
        agent_id=test_agent.id,
        task_id=uuid7(),
        data=CreateTaskRequest(
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            main=[{"evaluate": {"hi": "_"}}],
            metadata={"test": True},
        ),
        connection_pool=pool,
    )


@pytest.fixture
async def random_email():
    """Generate a random email address."""
    return f"{''.join([random.choice(string.ascii_lowercase) for _ in range(10)])}@mail.com"


@pytest.fixture
async def test_new_developer(pg_dsn, random_email):
    """Create a new test developer."""
    pool = await create_db_pool(dsn=pg_dsn)
    dev_id = uuid7()
    await create_developer(
        email=random_email,
        active=True,
        tags=["tag1"],
        settings={"key1": "val1"},
        developer_id=dev_id,
        connection_pool=pool,
    )

    return await get_developer(
        developer_id=dev_id,
        connection_pool=pool,
    )


@pytest.fixture
async def test_session(
    pg_dsn,
    test_developer_id,
    test_user,
    test_agent,
):
    """Create a test session."""
    pool = await create_db_pool(dsn=pg_dsn)
    return await create_session(
        developer_id=test_developer_id,
        data=CreateSessionRequest(
            agent=test_agent.id,
            user=test_user.id,
            metadata={"test": "test"},
            system_template="test system template",
        ),
        connection_pool=pool,
    )


@pytest.fixture
async def test_execution(
    pg_dsn,
    test_developer_id,
    test_task,
):
    """Create a test execution."""
    pool = await create_db_pool(dsn=pg_dsn)
    workflow_handle = WorkflowHandle(
        client=None,
        id="blah",
    )

    execution = await create_execution(
        developer_id=test_developer_id,
        task_id=test_task.id,
        data=CreateExecutionRequest(input={"test": "test"}),
        connection_pool=pool,
    )
    await create_temporal_lookup(
        execution_id=execution.id,
        workflow_handle=workflow_handle,
        connection_pool=pool,
    )
    yield execution


@pytest.fixture
def custom_scope_id():
    """Generate a custom scope ID."""
    return uuid7()


@pytest.fixture
async def test_execution_started(
    pg_dsn,
    test_developer_id,
    test_task,
    custom_scope_id,
):
    """Create a started test execution."""
    pool = await create_db_pool(dsn=pg_dsn)
    workflow_handle = WorkflowHandle(
        client=None,
        id="blah",
    )

    execution = await create_execution(
        developer_id=test_developer_id,
        task_id=test_task.id,
        data=CreateExecutionRequest(input={"test": "test"}),
        connection_pool=pool,
    )
    await create_temporal_lookup(
        execution_id=execution.id,
        workflow_handle=workflow_handle,
        connection_pool=pool,
    )

    actual_scope_id = custom_scope_id or uuid7()

    # Start the execution
    await create_execution_transition(
        developer_id=test_developer_id,
        execution_id=execution.id,
        data=CreateTransitionRequest(
            type="init",
            output={},
            current={"workflow": "main", "step": 0, "scope_id": actual_scope_id},
            next={"workflow": "main", "step": 0, "scope_id": actual_scope_id},
        ),
        connection_pool=pool,
    )
    yield execution


@pytest.fixture
async def test_transition(
    pg_dsn,
    test_developer_id,
    test_execution_started,
):
    """Create a test transition."""
    pool = await create_db_pool(dsn=pg_dsn)
    scope_id = uuid7()
    transition = await create_execution_transition(
        developer_id=test_developer_id,
        execution_id=test_execution_started.id,
        data=CreateTransitionRequest(
            type="step",
            output={},
            current={"workflow": "main", "step": 0, "scope_id": scope_id},
            next={"workflow": "wf1", "step": 1, "scope_id": scope_id},
        ),
        connection_pool=pool,
    )
    yield transition


@pytest.fixture
async def test_tool(
    pg_dsn,
    test_developer_id,
    test_agent,
):
    """Create a test tool."""
    pool = await create_db_pool(dsn=pg_dsn)
    function = {
        "description": "A function that prints hello world",
        "parameters": {"type": "object", "properties": {}},
    }

    tool_spec = {
        "function": function,
        "name": "hello_world1",
        "type": "function",
    }

    [tool, *_] = await create_tools(
        developer_id=test_developer_id,
        agent_id=test_agent.id,
        data=[CreateToolRequest(**tool_spec)],
        connection_pool=pool,
    )
    return tool


SAMPLE_MODELS = [
    {"id": "gpt-4"},
    {"id": "gpt-3.5-turbo"},
    {"id": "gpt-4o-mini"},
]


@pytest.fixture(scope="session")
def client(pg_dsn, localstack_container):
    """Test client fixture."""
    import os

    # Set S3 environment variables before creating TestClient
    os.environ["S3_ACCESS_KEY"] = localstack_container.env["AWS_ACCESS_KEY_ID"]
    os.environ["S3_SECRET_KEY"] = localstack_container.env["AWS_SECRET_ACCESS_KEY"]
    os.environ["S3_ENDPOINT"] = localstack_container.get_url()

    with (
        TestClient(app=app) as test_client,
        patch(
            "agents_api.routers.utils.model_validation.get_model_list",
            return_value=SAMPLE_MODELS,
        ),
    ):
        yield test_client

    # Clean up env vars
    for key in ["S3_ACCESS_KEY", "S3_SECRET_KEY", "S3_ENDPOINT"]:
        if key in os.environ:
            del os.environ[key]


@pytest.fixture
async def make_request(client, test_developer_id):
    """Factory fixture for making authenticated requests."""

    def _make_request(method, url, **kwargs):
        headers = kwargs.pop("headers", {})
        headers = {
            **headers,
            api_key_header_name: api_key,
        }

        if multi_tenant_mode:
            headers["X-Developer-Id"] = str(test_developer_id)

        headers["Content-Length"] = str(total_size(kwargs.get("json", {})))

        return client.request(method, url, headers=headers, **kwargs)

    return _make_request


@pytest.fixture(scope="session")
def localstack_container():
    """Session-scoped LocalStack container."""
    from testcontainers.localstack import LocalStackContainer

    localstack = LocalStackContainer(image="localstack/localstack:s3-latest").with_services(
        "s3"
    )
    localstack.start()

    try:
        yield localstack
    finally:
        localstack.stop()


@pytest.fixture(autouse=True, scope="session")
def disable_s3_cache():
    """Disable async_s3 cache during tests to avoid event loop issues."""
    from agents_api.clients import async_s3

    # Check if the functions are wrapped with alru_cache
    if hasattr(async_s3.setup, "__wrapped__"):
        # Save original functions
        original_setup = async_s3.setup.__wrapped__
        original_exists = async_s3.exists.__wrapped__
        original_list_buckets = async_s3.list_buckets.__wrapped__

        # Replace cached functions with uncached versions
        async_s3.setup = original_setup
        async_s3.exists = original_exists
        async_s3.list_buckets = original_list_buckets

    yield


@pytest.fixture
async def s3_client(localstack_container):
    """S3 client fixture that works with TestClient's event loop."""
    from contextlib import AsyncExitStack

    from aiobotocore.session import get_session

    # AIDEV-NOTE: Fixed S3 client fixture with proper LocalStack integration
    # to resolve NoSuchKey errors in file route tests

    # Create async S3 client using LocalStack
    session = get_session()

    async with AsyncExitStack() as stack:
        client = await stack.enter_async_context(
            session.create_client(
                "s3",
                aws_access_key_id=localstack_container.env["AWS_ACCESS_KEY_ID"],
                aws_secret_access_key=localstack_container.env["AWS_SECRET_ACCESS_KEY"],
                endpoint_url=localstack_container.get_url(),
                region_name="us-east-1",
            )
        )

        # Ensure default bucket exists
        try:
            await client.head_bucket(Bucket="default")
        except Exception:
            with contextlib.suppress(Exception):
                await client.create_bucket(Bucket="default")  # Bucket might already exist

        yield client


@pytest.fixture
async def clean_secrets(pg_dsn, test_developer_id):
    """Fixture to clean up secrets before and after tests."""

    async def purge() -> None:
        pool = await create_db_pool(dsn=pg_dsn)
        try:
            secrets = await list_secrets(
                developer_id=test_developer_id,
                connection_pool=pool,
            )
            for secret in secrets:
                await delete_secret(
                    secret_id=secret.id,
                    developer_id=test_developer_id,
                    connection_pool=pool,
                )
        finally:
            # pool is closed in *the same* loop it was created in
            await pool.close()

    await purge()
    yield
    await purge()


# Markers for test categorization
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "workflow: marks tests as workflow tests")
