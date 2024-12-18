import json
import random
import string
import time
from uuid import UUID

import asyncpg
from fastapi.testclient import TestClient
from temporalio.client import WorkflowHandle
from uuid_extensions import uuid7
from ward import fixture

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
from agents_api.queries.developers.create_developer import create_developer

# from agents_api.queries.agents.create_agent import create_agent
# from agents_api.queries.agents.delete_agent import delete_agent
from agents_api.queries.developers.get_developer import get_developer

# from agents_api.queries.docs.create_doc import create_doc
# from agents_api.queries.docs.delete_doc import delete_doc
# from agents_api.queries.execution.create_execution import create_execution
# from agents_api.queries.execution.create_execution_transition import create_execution_transition
# from agents_api.queries.execution.create_temporal_lookup import create_temporal_lookup
# from agents_api.queries.files.create_file import create_file
# from agents_api.queries.files.delete_file import delete_file
# from agents_api.queries.session.create_session import create_session
# from agents_api.queries.session.delete_session import delete_session
# from agents_api.queries.task.create_task import create_task
# from agents_api.queries.task.delete_task import delete_task
# from agents_api.queries.tools.create_tools import create_tools
# from agents_api.queries.tools.delete_tool import delete_tool
from agents_api.queries.users.create_user import create_user
from agents_api.queries.users.delete_user import delete_user

from agents_api.web import app

from .utils import (
    get_pg_dsn,
    patch_s3_client,
)
from .utils import (
    patch_embed_acompletion as patch_embed_acompletion_ctx,
)

EMBEDDING_SIZE: int = 1024


@fixture(scope="global")
def pg_dsn():
    with get_pg_dsn() as pg_dsn:
        yield pg_dsn


@fixture(scope="global")
def test_developer_id():
    if not multi_tenant_mode:
        return UUID(int=0)

    developer_id = uuid7()
    return developer_id


# @fixture(scope="global")
# async def test_file(dsn=pg_dsn, developer_id=test_developer_id):
#     async with get_pg_client(dsn=dsn) as client:
#         file = await create_file(
#             developer_id=developer_id,
#             data=CreateFileRequest(
#                 name="Hello",
#                 description="World",
#                 mime_type="text/plain",
#                 content="eyJzYW1wbGUiOiAidGVzdCJ9",
#             ),
#             client=client,
#         )
#         yield file


@fixture(scope="global")
async def test_developer(dsn=pg_dsn, developer_id=test_developer_id):
    pool = await create_db_pool(dsn=dsn)
    developer = await get_developer(
        developer_id=developer_id,
        connection_pool=pool,
    )

    return developer


@fixture(scope="test")
def patch_embed_acompletion():
    output = {"role": "assistant", "content": "Hello, world!"}
    with patch_embed_acompletion_ctx(output) as (embed, acompletion):
        yield embed, acompletion


# @fixture(scope="global")
# async def test_agent(dsn=pg_dsn, developer_id=test_developer_id):
#     async with get_pg_client(dsn=dsn) as client:
#         agent = await create_agent(
#             developer_id=developer_id,
#             data=CreateAgentRequest(
#                 model="gpt-4o-mini",
#                 name="test agent",
#                 about="test agent about",
#                 metadata={"test": "test"},
#             ),
#             client=client,
#         )
#         yield agent


@fixture(scope="global")
async def test_user(dsn=pg_dsn, developer=test_developer):
    pool = await create_db_pool(dsn=dsn)

    user = await create_user(
        developer_id=developer.id,
        data=CreateUserRequest(
            name="test user",
            about="test user about",
        ),
        connection_pool=pool,
    )

    return user


@fixture(scope="test")
async def random_email():
    return f"{"".join([random.choice(string.ascii_lowercase) for _ in range(10)])}@mail.com"


@fixture(scope="test")
async def test_new_developer(dsn=pg_dsn, email=random_email):
    pool = await create_db_pool(dsn=dsn)
    dev_id = uuid7()
    developer = await create_developer(
        email=email,
        active=True,
        tags=["tag1"],
        settings={"key1": "val1"},
        developer_id=dev_id,
        connection_pool=pool,
    )

    return developer


# @fixture(scope="global")
# async def test_session(
#     dsn=pg_dsn,
#     developer_id=test_developer_id,
#     test_user=test_user,
#     test_agent=test_agent,
# ):
#     async with get_pg_client(dsn=dsn) as client:
#         session = await create_session(
#             developer_id=developer_id,
#             data=CreateSessionRequest(
#                 agent=test_agent.id, user=test_user.id, metadata={"test": "test"}
#             ),
#             client=client,
#         )
#         yield session


# @fixture(scope="global")
# async def test_doc(
#     dsn=pg_dsn,
#     developer_id=test_developer_id,
#     agent=test_agent,
# ):
#     async with get_pg_client(dsn=dsn) as client:
#         doc = await create_doc(
#             developer_id=developer_id,
#             owner_type="agent",
#             owner_id=agent.id,
#             data=CreateDocRequest(title="Hello", content=["World"]),
#             client=client,
#         )
#         yield doc


# @fixture(scope="global")
# async def test_user_doc(
#     dsn=pg_dsn,
#     developer_id=test_developer_id,
#     user=test_user,
# ):
#     async with get_pg_client(dsn=dsn) as client:
#         doc = await create_doc(
#             developer_id=developer_id,
#             owner_type="user",
#             owner_id=user.id,
#             data=CreateDocRequest(title="Hello", content=["World"]),
#             client=client,
#         )
#         yield doc


# @fixture(scope="global")
# async def test_task(
#     dsn=pg_dsn,
#     developer_id=test_developer_id,
#     agent=test_agent,
# ):
#     async with get_pg_client(dsn=dsn) as client:
#         task = await create_task(
#             developer_id=developer_id,
#             agent_id=agent.id,
#             data=CreateTaskRequest(
#                 **{
#                     "name": "test task",
#                     "description": "test task about",
#                     "input_schema": {"type": "object", "additionalProperties": True},
#                     "main": [{"evaluate": {"hello": '"world"'}}],
#                 }
#             ),
#             client=client,
#         )
#         yield task


# @fixture(scope="global")
# async def test_execution(
#     dsn=pg_dsn,
#     developer_id=test_developer_id,
#     task=test_task,
# ):
#     workflow_handle = WorkflowHandle(
#         client=None,
#         id="blah",
#     )

#     async with get_pg_client(dsn=dsn) as client:
#         execution = await create_execution(
#             developer_id=developer_id,
#             task_id=task.id,
#             data=CreateExecutionRequest(input={"test": "test"}),
#             client=client,
#         )
#         await create_temporal_lookup(
#             developer_id=developer_id,
#             execution_id=execution.id,
#             workflow_handle=workflow_handle,
#             client=client,
#         )
#         yield execution


# @fixture(scope="test")
# async def test_execution_started(
#     dsn=pg_dsn,
#     developer_id=test_developer_id,
#     task=test_task,
# ):
#     workflow_handle = WorkflowHandle(
#         client=None,
#         id="blah",
#     )

#     async with get_pg_client(dsn=dsn) as client:
#         execution = await create_execution(
#             developer_id=developer_id,
#             task_id=task.id,
#             data=CreateExecutionRequest(input={"test": "test"}),
#             client=client,
#         )
#         await create_temporal_lookup(
#             developer_id=developer_id,
#             execution_id=execution.id,
#             workflow_handle=workflow_handle,
#             client=client,
#         )

#         # Start the execution
#         await create_execution_transition(
#             developer_id=developer_id,
#             task_id=task.id,
#             execution_id=execution.id,
#             data=CreateTransitionRequest(
#                 type="init",
#                 output={},
#                 current={"workflow": "main", "step": 0},
#                 next={"workflow": "main", "step": 0},
#             ),
#             update_execution_status=True,
#             client=client,
#         )
#         yield execution


# @fixture(scope="global")
# async def test_transition(
#     dsn=pg_dsn,
#     developer_id=test_developer_id,
#     execution=test_execution,
# ):
#     async with get_pg_client(dsn=dsn) as client:
#         transition = await create_execution_transition(
#             developer_id=developer_id,
#             execution_id=execution.id,
#             data=CreateTransitionRequest(
#                 type="step",
#                 output={},
#                 current={"workflow": "main", "step": 0},
#                 next={"workflow": "wf1", "step": 1},
#             ),
#             client=client,
#         )
#         yield transition


# @fixture(scope="global")
# async def test_tool(
#     dsn=pg_dsn,
#     developer_id=test_developer_id,
#     agent=test_agent,
# ):
#     function = {
#         "description": "A function that prints hello world",
#         "parameters": {"type": "object", "properties": {}},
#     }

#     tool = {
#         "function": function,
#         "name": "hello_world1",
#         "type": "function",
#     }

#     [tool, *_] = await create_tools(
#         developer_id=developer_id,
#         agent_id=agent.id,
#         data=[CreateToolRequest(**tool)],
#         connection_pool=pool,
#     )
#     yield tool

#     # Cleanup
#     try:
#         await delete_tool(
#             developer_id=developer_id,
#             tool_id=tool.id,
#             connection_pool=pool,
#         )
#     finally:
#         await pool.close()


@fixture(scope="global")
async def client(dsn=pg_dsn):
    pool = await create_db_pool(dsn=dsn)

    client = TestClient(app=app)
    client.state.postgres_pool = pool
    return client


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

        return client.request(method, url, headers=headers, **kwargs)

    return _make_request


@fixture(scope="global")
def s3_client():
    with patch_s3_client() as s3_client:
        yield s3_client
