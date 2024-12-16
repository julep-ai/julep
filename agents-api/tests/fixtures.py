import time
from uuid import UUID

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
from agents_api.env import api_key, api_key_header_name, multi_tenant_mode

# from agents_api.queries.agents.create_agent import create_agent
# from agents_api.queries.agents.delete_agent import delete_agent
from agents_api.queries.developers.get_developer import get_developer

# from agents_api.queries.docs.create_doc import create_doc
# from agents_api.queries.docs.delete_doc import delete_doc
# from agents_api.queries.execution.create_execution import create_execution
# from agents_api.queries.execution.create_execution_transition import (
#     create_execution_transition,
# )
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

# from agents_api.web import app
from .utils import (
    patch_embed_acompletion as patch_embed_acompletion_ctx,
)
from .utils import (
    patch_pg_client,
    patch_s3_client,
)

EMBEDDING_SIZE: int = 1024


@fixture(scope="global")
async def pg_client():
    async with patch_pg_client() as pg_client:
        yield pg_client


@fixture(scope="global")
def test_developer_id():
    if not multi_tenant_mode:
        yield UUID(int=0)
        return

    developer_id = uuid7()

    yield developer_id


# @fixture(scope="global")
# def test_file(client=pg_client, developer_id=test_developer_id):
#     file = create_file(
#         developer_id=developer_id,
#         data=CreateFileRequest(
#             name="Hello",
#             description="World",
#             mime_type="text/plain",
#             content="eyJzYW1wbGUiOiAidGVzdCJ9",
#         ),
#         client=client,
#     )

#     yield file


@fixture(scope="global")
async def test_developer(pg_client=pg_client, developer_id=test_developer_id):
    return await get_developer(
        developer_id=developer_id,
        client=pg_client,
    )


@fixture(scope="test")
def patch_embed_acompletion():
    output = {"role": "assistant", "content": "Hello, world!"}

    with patch_embed_acompletion_ctx(output) as (embed, acompletion):
        yield embed, acompletion


# @fixture(scope="global")
# def test_agent(pg_client=pg_client, developer_id=test_developer_id):
#     agent = create_agent(
#         developer_id=developer_id,
#         data=CreateAgentRequest(
#             model="gpt-4o-mini",
#             name="test agent",
#             about="test agent about",
#             metadata={"test": "test"},
#         ),
#         client=pg_client,
#     )

#     yield agent


@fixture(scope="global")
def test_user(pg_client=pg_client, developer_id=test_developer_id):
    user = create_user(
        developer_id=developer_id,
        data=CreateUserRequest(
            name="test user",
            about="test user about",
        ),
        client=pg_client,
    )

    yield user


# @fixture(scope="global")
# def test_session(
#     pg_client=pg_client,
#     developer_id=test_developer_id,
#     test_user=test_user,
#     test_agent=test_agent,
# ):
#     session = create_session(
#         developer_id=developer_id,
#         data=CreateSessionRequest(
#             agent=test_agent.id, user=test_user.id, metadata={"test": "test"}
#         ),
#         client=pg_client,
#     )

#     yield session


# @fixture(scope="global")
# def test_doc(
#     client=pg_client,
#     developer_id=test_developer_id,
#     agent=test_agent,
# ):
#     doc = create_doc(
#         developer_id=developer_id,
#         owner_type="agent",
#         owner_id=agent.id,
#         data=CreateDocRequest(title="Hello", content=["World"]),
#         client=client,
#     )

#     yield doc


# @fixture(scope="global")
# def test_user_doc(
#     client=pg_client,
#     developer_id=test_developer_id,
#     user=test_user,
# ):
#     doc = create_doc(
#         developer_id=developer_id,
#         owner_type="user",
#         owner_id=user.id,
#         data=CreateDocRequest(title="Hello", content=["World"]),
#         client=client,
#     )

#     yield doc


# @fixture(scope="global")
# def test_task(
#     client=pg_client,
#     developer_id=test_developer_id,
#     agent=test_agent,
# ):
#     task = create_task(
#         developer_id=developer_id,
#         agent_id=agent.id,
#         data=CreateTaskRequest(
#             **{
#                 "name": "test task",
#                 "description": "test task about",
#                 "input_schema": {"type": "object", "additionalProperties": True},
#                 "main": [{"evaluate": {"hello": '"world"'}}],
#             }
#         ),
#         client=client,
#     )

#     yield task


# @fixture(scope="global")
# def test_execution(
#     client=pg_client,
#     developer_id=test_developer_id,
#     task=test_task,
# ):
#     workflow_handle = WorkflowHandle(
#         client=None,
#         id="blah",
#     )

#     execution = create_execution(
#         developer_id=developer_id,
#         task_id=task.id,
#         data=CreateExecutionRequest(input={"test": "test"}),
#         client=client,
#     )
#     create_temporal_lookup(
#         developer_id=developer_id,
#         execution_id=execution.id,
#         workflow_handle=workflow_handle,
#         client=client,
#     )

#     yield execution


# @fixture(scope="test")
# def test_execution_started(
#     client=pg_client,
#     developer_id=test_developer_id,
#     task=test_task,
# ):
#     workflow_handle = WorkflowHandle(
#         client=None,
#         id="blah",
#     )

#     execution = create_execution(
#         developer_id=developer_id,
#         task_id=task.id,
#         data=CreateExecutionRequest(input={"test": "test"}),
#         client=client,
#     )
#     create_temporal_lookup(
#         developer_id=developer_id,
#         execution_id=execution.id,
#         workflow_handle=workflow_handle,
#         client=client,
#     )

#     # Start the execution
#     create_execution_transition(
#         developer_id=developer_id,
#         task_id=task.id,
#         execution_id=execution.id,
#         data=CreateTransitionRequest(
#             type="init",
#             output={},
#             current={"workflow": "main", "step": 0},
#             next={"workflow": "main", "step": 0},
#         ),
#         update_execution_status=True,
#         client=client,
#     )

#     yield execution


# @fixture(scope="global")
# def test_transition(
#     client=pg_client,
#     developer_id=test_developer_id,
#     execution=test_execution,
# ):
#     transition = create_execution_transition(
#         developer_id=developer_id,
#         execution_id=execution.id,
#         data=CreateTransitionRequest(
#             type="step",
#             output={},
#             current={"workflow": "main", "step": 0},
#             next={"workflow": "wf1", "step": 1},
#         ),
#         client=client,
#     )

#     yield transition


# @fixture(scope="global")
# def test_tool(
#     client=pg_client,
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

#     [tool, *_] = create_tools(
#         developer_id=developer_id,
#         agent_id=agent.id,
#         data=[CreateToolRequest(**tool)],
#         client=client,
#     )
#
#     yield tool


# @fixture(scope="global")
# def client(pg_client=pg_client):
#     client = TestClient(app=app)
#     client.state.pg_client = pg_client

#     return client

# @fixture(scope="global")
# def make_request(client=client, developer_id=test_developer_id):
#     def _make_request(method, url, **kwargs):
#         headers = kwargs.pop("headers", {})
#         headers = {
#             **headers,
#             api_key_header_name: api_key,
#         }

#         if multi_tenant_mode:
#             headers["X-Developer-Id"] = str(developer_id)

#         return client.request(method, url, headers=headers, **kwargs)

#     return _make_request


@fixture(scope="global")
def s3_client():
    with patch_s3_client() as s3_client:
        yield s3_client
