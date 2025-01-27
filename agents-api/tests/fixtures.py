import os
import random
import string
import sys
from unittest.mock import patch
from uuid import UUID

from agents_api.autogen.openapi_model import (
    CreateAgentRequest,
    CreateDocRequest,
    CreateExecutionRequest,
    CreateFileRequest,
    CreateSessionRequest,
    CreateTaskRequest,
    CreateToolRequest,
    CreateTransitionRequest,
    CreateUserRequest,
)
from agents_api.clients.pg import create_db_pool
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
from agents_api.queries.sessions.create_session import create_session
from agents_api.queries.tasks.create_task import create_task
from agents_api.queries.tools.create_tools import create_tools
from agents_api.queries.users.create_user import create_user
from agents_api.web import app
from aiobotocore.session import get_session
from fastapi.testclient import TestClient
from temporalio.client import WorkflowHandle
from uuid_extensions import uuid7
from ward import fixture

from .utils import (
    get_localstack,
    get_pg_dsn,
    make_vector_with_similarity,
)
from .utils import (
    patch_embed_acompletion as patch_embed_acompletion_ctx,
)


@fixture(scope="global")
def pg_dsn():
    with get_pg_dsn() as pg_dsn:
        os.environ["PG_DSN"] = pg_dsn

        try:
            yield pg_dsn
        finally:
            del os.environ["PG_DSN"]


@fixture(scope="global")
def test_developer_id():
    if not multi_tenant_mode:
        return UUID(int=0)

    return uuid7()


@fixture(scope="global")
async def test_developer(dsn=pg_dsn, developer_id=test_developer_id):
    pool = await create_db_pool(dsn=dsn)
    return await get_developer(
        developer_id=developer_id,
        connection_pool=pool,
    )


@fixture(scope="test")
def patch_embed_acompletion():
    output = {"role": "assistant", "content": "Hello, world!"}
    with patch_embed_acompletion_ctx(output) as (embed, acompletion):
        yield embed, acompletion


@fixture(scope="test")
async def test_agent(dsn=pg_dsn, developer=test_developer):
    pool = await create_db_pool(dsn=dsn)

    return await create_agent(
        developer_id=developer.id,
        data=CreateAgentRequest(
            model="gpt-4o-mini",
            name="test agent",
            about="test agent about",
            metadata={"test": "test"},
        ),
        connection_pool=pool,
    )


@fixture(scope="test")
async def test_user(dsn=pg_dsn, developer=test_developer):
    pool = await create_db_pool(dsn=dsn)

    return await create_user(
        developer_id=developer.id,
        data=CreateUserRequest(
            name="test user",
            about="test user about",
        ),
        connection_pool=pool,
    )


@fixture(scope="test")
async def test_file(dsn=pg_dsn, developer=test_developer, user=test_user):
    pool = await create_db_pool(dsn=dsn)
    return await create_file(
        developer_id=developer.id,
        data=CreateFileRequest(
            name="Hello",
            description="World",
            mime_type="text/plain",
            content="eyJzYW1wbGUiOiAidGVzdCJ9",
        ),
        connection_pool=pool,
    )


@fixture(scope="test")
async def test_doc(dsn=pg_dsn, developer=test_developer, agent=test_agent):
    pool = await create_db_pool(dsn=dsn)
    resp = await create_doc(
        developer_id=developer.id,
        data=CreateDocRequest(
            title="Hello",
            content=["World", "World2", "World3"],
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="agent",
        owner_id=agent.id,
        connection_pool=pool,
    )

    # Explicitly Refresh Indices: After inserting data, run a command to refresh the index,
    # ensuring it's up-to-date before executing queries.
    # This can be achieved by executing a REINDEX command
    await pool.execute("REINDEX DATABASE")

    yield await get_doc(developer_id=developer.id, doc_id=resp.id, connection_pool=pool)

    # TODO: Delete the doc
    # await delete_doc(
    #     developer_id=developer.id,
    #     doc_id=resp.id,
    #     owner_type="agent",
    #     owner_id=agent.id,
    #     connection_pool=pool,
    # )


@fixture(scope="test")
async def test_doc_with_embedding(dsn=pg_dsn, developer=test_developer, doc=test_doc):
    pool = await create_db_pool(dsn=dsn)
    embedding_with_confidence_0 = make_vector_with_similarity(d=0.0)
    embedding_with_confidence_05 = make_vector_with_similarity(d=0.5)
    embedding_with_confidence_05_neg = make_vector_with_similarity(d=-0.5)
    embedding_with_confidence_1_neg = make_vector_with_similarity(d=-1.0)
    await pool.execute(
        """
        INSERT INTO docs_embeddings_store (developer_id, doc_id, index, chunk_seq, chunk, embedding)
        VALUES ($1, $2, 0, 0, $3, $4)
    """,
        developer.id,
        doc.id,
        doc.content[0] if isinstance(doc.content, list) else doc.content,
        f"[{', '.join([str(x) for x in [1.0] * 1024])}]",
    )

    # Insert embedding with confidence 0 with respect to unit vector
    await pool.execute(
        """
        INSERT INTO docs_embeddings_store (developer_id, doc_id, index, chunk_seq, chunk, embedding)
        VALUES ($1, $2, 0, 1, $3, $4)
        """,
        developer.id,
        doc.id,
        "Test content 1",
        f"[{', '.join([str(x) for x in embedding_with_confidence_0])}]",
    )

    # Insert embedding with confidence 0.5 with respect to unit vector
    await pool.execute(
        """
        INSERT INTO docs_embeddings_store (developer_id, doc_id, index, chunk_seq, chunk, embedding)
        VALUES ($1, $2, 0, 2, $3, $4)
        """,
        developer.id,
        doc.id,
        "Test content 2",
        f"[{', '.join([str(x) for x in embedding_with_confidence_05])}]",
    )

    # Insert embedding with confidence -0.5 with respect to unit vector
    await pool.execute(
        """
        INSERT INTO docs_embeddings_store (developer_id, doc_id, index, chunk_seq, chunk, embedding)
        VALUES ($1, $2, 0, 3, $3, $4)
        """,
        developer.id,
        doc.id,
        "Test content 3",
        f"[{', '.join([str(x) for x in embedding_with_confidence_05_neg])}]",
    )

    # Insert embedding with confidence -1 with respect to unit vector
    await pool.execute(
        """
        INSERT INTO docs_embeddings_store (developer_id, doc_id, index, chunk_seq, chunk, embedding)
        VALUES ($1, $2, 0, 4, $3, $4)
        """,
        developer.id,
        doc.id,
        "Test content 4",
        f"[{', '.join([str(x) for x in embedding_with_confidence_1_neg])}]",
    )

    yield await get_doc(developer_id=developer.id, doc_id=doc.id, connection_pool=pool)


@fixture(scope="test")
async def test_user_doc(dsn=pg_dsn, developer=test_developer, user=test_user):
    pool = await create_db_pool(dsn=dsn)
    resp = await create_doc(
        developer_id=developer.id,
        data=CreateDocRequest(
            title="Hello",
            content=["World", "World2", "World3"],
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="user",
        owner_id=user.id,
        connection_pool=pool,
    )

    # Explicitly Refresh Indices: After inserting data, run a command to refresh the index,
    # ensuring it's up-to-date before executing queries.
    # This can be achieved by executing a REINDEX command
    await pool.execute("REINDEX DATABASE")

    yield await get_doc(developer_id=developer.id, doc_id=resp.id, connection_pool=pool)

    # TODO: Delete the doc
    # await delete_doc(
    #     developer_id=developer.id,
    #     doc_id=resp.id,
    #     owner_type="user",
    #     owner_id=user.id,
    #     connection_pool=pool,
    # )


@fixture(scope="test")
async def test_task(dsn=pg_dsn, developer=test_developer, agent=test_agent):
    pool = await create_db_pool(dsn=dsn)
    return await create_task(
        developer_id=developer.id,
        agent_id=agent.id,
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


@fixture(scope="test")
async def random_email():
    return f"{''.join([random.choice(string.ascii_lowercase) for _ in range(10)])}@mail.com"


@fixture(scope="test")
async def test_new_developer(dsn=pg_dsn, email=random_email):
    pool = await create_db_pool(dsn=dsn)
    dev_id = uuid7()
    await create_developer(
        email=email,
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


@fixture(scope="test")
async def test_session(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    test_user=test_user,
    test_agent=test_agent,
):
    pool = await create_db_pool(dsn=dsn)

    return await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=test_agent.id,
            user=test_user.id,
            metadata={"test": "test"},
            system_template="test system template",
        ),
        connection_pool=pool,
    )


@fixture(scope="global")
async def test_execution(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    task=test_task,
):
    pool = await create_db_pool(dsn=dsn)
    workflow_handle = WorkflowHandle(
        client=None,
        id="blah",
    )

    execution = await create_execution(
        developer_id=developer_id,
        task_id=task.id,
        data=CreateExecutionRequest(input={"test": "test"}),
        connection_pool=pool,
    )
    await create_temporal_lookup(
        execution_id=execution.id,
        workflow_handle=workflow_handle,
        connection_pool=pool,
    )
    yield execution


@fixture(scope="test")
async def test_execution_started(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    task=test_task,
):
    pool = await create_db_pool(dsn=dsn)
    workflow_handle = WorkflowHandle(
        client=None,
        id="blah",
    )

    execution = await create_execution(
        developer_id=developer_id,
        task_id=task.id,
        data=CreateExecutionRequest(input={"test": "test"}),
        connection_pool=pool,
    )
    await create_temporal_lookup(
        execution_id=execution.id,
        workflow_handle=workflow_handle,
        connection_pool=pool,
    )

    # Start the execution
    await create_execution_transition(
        developer_id=developer_id,
        execution_id=execution.id,
        data=CreateTransitionRequest(
            type="init",
            output={},
            current={"workflow": "main", "step": 0},
            next={"workflow": "main", "step": 0},
        ),
        connection_pool=pool,
    )
    yield execution


@fixture(scope="global")
async def test_transition(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    execution=test_execution_started,
):
    pool = await create_db_pool(dsn=dsn)
    transition = await create_execution_transition(
        developer_id=developer_id,
        execution_id=execution.id,
        data=CreateTransitionRequest(
            type="step",
            output={},
            current={"workflow": "main", "step": 0},
            next={"workflow": "wf1", "step": 1},
        ),
        connection_pool=pool,
    )
    yield transition


@fixture(scope="test")
async def test_tool(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    pool = await create_db_pool(dsn=dsn)
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
        developer_id=developer_id,
        agent_id=agent.id,
        data=[CreateToolRequest(**tool_spec)],
        connection_pool=pool,
    )
    return tool


SAMPLE_MODELS = [
    {"id": "gpt-4"},
    {"id": "gpt-3.5-turbo"},
    {"id": "gpt-4o-mini"},
]


@fixture(scope="global")
def client(_dsn=pg_dsn):
    with (
        TestClient(app=app) as client,
        patch(
            "agents_api.routers.utils.model_validation.get_model_list",
            return_value=SAMPLE_MODELS,
        ),
    ):
        yield client


@fixture(scope="global")
async def make_request(client=client, developer_id=test_developer_id):
    def _make_request(method, url, **kwargs):
        headers = kwargs.pop("headers", {})
        headers = {
            **headers,
            api_key_header_name: api_key,
        }

        if multi_tenant_mode:
            headers["X-Developer-Id"] = str(developer_id)

        headers["Content-Length"] = str(sys.getsizeof(kwargs.get("json", {})))

        return client.request(method, url, headers=headers, **kwargs)

    return _make_request


@fixture(scope="global")
async def s3_client():
    with get_localstack() as localstack:
        s3_endpoint = localstack.get_url()

        session = get_session()
        s3_client = await session.create_client(
            "s3",
            endpoint_url=s3_endpoint,
            aws_access_key_id=localstack.env["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=localstack.env["AWS_SECRET_ACCESS_KEY"],
        ).__aenter__()

        app.state.s3_client = s3_client

        try:
            yield s3_client
        finally:
            await s3_client.close()
            app.state.s3_client = None
