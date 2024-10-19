import time
from uuid import UUID, uuid4

from cozo_migrate.api import apply, init
from fastapi.testclient import TestClient
from pycozo import Client as CozoClient
from temporalio.client import WorkflowHandle
from ward import fixture

from agents_api.autogen.openapi_model import (
    CreateAgentRequest,
    CreateDocRequest,
    CreateExecutionRequest,
    CreateSessionRequest,
    CreateTaskRequest,
    CreateToolRequest,
    CreateTransitionRequest,
    CreateUserRequest,
)
from agents_api.env import api_key, api_key_header_name, multi_tenant_mode
from agents_api.models.agent.create_agent import create_agent
from agents_api.models.agent.delete_agent import delete_agent
from agents_api.models.developer.get_developer import get_developer
from agents_api.models.docs.create_doc import create_doc
from agents_api.models.docs.delete_doc import delete_doc
from agents_api.models.execution.create_execution import create_execution
from agents_api.models.execution.create_execution_transition import (
    create_execution_transition,
)
from agents_api.models.execution.create_temporal_lookup import create_temporal_lookup
from agents_api.models.session.create_session import create_session
from agents_api.models.session.delete_session import delete_session
from agents_api.models.task.create_task import create_task
from agents_api.models.task.delete_task import delete_task
from agents_api.models.tools.create_tools import create_tools
from agents_api.models.tools.delete_tool import delete_tool
from agents_api.models.user.create_user import create_user
from agents_api.models.user.delete_user import delete_user
from agents_api.web import app
from tests.utils import patch_embed_acompletion as patch_embed_acompletion_ctx

EMBEDDING_SIZE: int = 1024


@fixture(scope="global")
def cozo_client(migrations_dir: str = "./migrations"):
    # Create a new client for each test
    # and initialize the schema.
    client = CozoClient()

    setattr(app.state, "cozo_client", client)

    init(client)
    apply(client, migrations_dir=migrations_dir, all_=True)

    return client


@fixture(scope="global")
def test_developer_id(cozo_client=cozo_client):
    if not multi_tenant_mode:
        yield UUID(int=0)
        return

    developer_id = uuid4()

    cozo_client.run(
        f"""
    ?[developer_id, email, settings] <- [["{str(developer_id)}", "developers@julep.ai", {{}}]]
    :insert developers {{ developer_id, email, settings }}
    """
    )

    yield developer_id

    cozo_client.run(
        f"""
    ?[developer_id, email] <- [["{str(developer_id)}", "developers@julep.ai"]]
    :delete developers {{ developer_id, email }}
    """
    )


@fixture(scope="global")
def test_developer(cozo_client=cozo_client, developer_id=test_developer_id):
    return get_developer(
        developer_id=developer_id,
        client=cozo_client,
    )


@fixture(scope="test")
def patch_embed_acompletion():
    output = {"role": "assistant", "content": "Hello, world!"}

    with patch_embed_acompletion_ctx(output) as (embed, acompletion):
        yield embed, acompletion


@fixture(scope="global")
def test_agent(cozo_client=cozo_client, developer_id=test_developer_id):
    agent = create_agent(
        developer_id=developer_id,
        data=CreateAgentRequest(
            model="gpt-4o-mini",
            name="test agent",
            about="test agent about",
            metadata={"test": "test"},
        ),
        client=cozo_client,
    )

    yield agent

    delete_agent(
        developer_id=developer_id,
        agent_id=agent.id,
        client=cozo_client,
    )


@fixture(scope="global")
def test_user(cozo_client=cozo_client, developer_id=test_developer_id):
    user = create_user(
        developer_id=developer_id,
        data=CreateUserRequest(
            name="test user",
            about="test user about",
        ),
        client=cozo_client,
    )

    yield user

    delete_user(
        developer_id=developer_id,
        user_id=user.id,
        client=cozo_client,
    )


@fixture(scope="global")
def test_session(
    cozo_client=cozo_client,
    developer_id=test_developer_id,
    test_user=test_user,
    test_agent=test_agent,
):
    session = create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=test_agent.id,
            user=test_user.id,
        ),
        client=cozo_client,
    )

    yield session

    delete_session(
        developer_id=developer_id,
        session_id=session.id,
        client=cozo_client,
    )


@fixture(scope="global")
def test_doc(
    client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
):
    doc = create_doc(
        developer_id=developer_id,
        owner_type="agent",
        owner_id=agent.id,
        data=CreateDocRequest(title="Hello", content=["World"]),
        client=client,
    )

    time.sleep(0.5)

    yield doc

    delete_doc(
        developer_id=developer_id,
        doc_id=doc.id,
        owner_type="agent",
        owner_id=agent.id,
        client=client,
    )


@fixture(scope="global")
def test_user_doc(
    client=cozo_client,
    developer_id=test_developer_id,
    user=test_user,
):
    doc = create_doc(
        developer_id=developer_id,
        owner_type="user",
        owner_id=user.id,
        data=CreateDocRequest(title="Hello", content=["World"]),
        client=client,
    )

    yield doc

    delete_doc(
        developer_id=developer_id,
        doc_id=doc.id,
        owner_type="user",
        owner_id=user.id,
        client=client,
    )


@fixture(scope="global")
def test_task(
    client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
):
    task = create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            **{
                "name": "test task",
                "description": "test task about",
                "input_schema": {"type": "object", "additionalProperties": True},
                "main": [{"evaluate": {"hello": '"world"'}}],
            }
        ),
        client=client,
    )

    yield task

    delete_task(
        developer_id=developer_id,
        task_id=task.id,
        client=client,
    )


@fixture(scope="global")
def test_execution(
    client=cozo_client,
    developer_id=test_developer_id,
    task=test_task,
):
    workflow_handle = WorkflowHandle(
        client=None,
        id="blah",
    )

    execution = create_execution(
        developer_id=developer_id,
        task_id=task.id,
        data=CreateExecutionRequest(input={"test": "test"}),
        client=client,
    )
    create_temporal_lookup(
        developer_id=developer_id,
        execution_id=execution.id,
        workflow_handle=workflow_handle,
        client=client,
    )

    yield execution

    client.run(
        f"""
    ?[execution_id] <- ["{str(execution.id)}"]
    :delete executions {{ execution_id  }}
    """
    )


@fixture(scope="test")
def test_execution_started(
    client=cozo_client,
    developer_id=test_developer_id,
    task=test_task,
):
    workflow_handle = WorkflowHandle(
        client=None,
        id="blah",
    )

    execution = create_execution(
        developer_id=developer_id,
        task_id=task.id,
        data=CreateExecutionRequest(input={"test": "test"}),
        client=client,
    )
    create_temporal_lookup(
        developer_id=developer_id,
        execution_id=execution.id,
        workflow_handle=workflow_handle,
        client=client,
    )

    # Start the execution
    create_execution_transition(
        developer_id=developer_id,
        task_id=task.id,
        execution_id=execution.id,
        data=CreateTransitionRequest(
            type="init",
            output={},
            current={"workflow": "main", "step": 0},
            next={"workflow": "main", "step": 0},
        ),
        update_execution_status=True,
        client=client,
    )

    yield execution

    client.run(
        f"""
    ?[execution_id, task_id] <- [[to_uuid("{str(execution.id)}"), to_uuid("{str(task.id)}")]]
    :delete executions {{ execution_id, task_id }}
    """
    )


@fixture(scope="global")
def test_transition(
    client=cozo_client,
    developer_id=test_developer_id,
    execution=test_execution,
):
    transition = create_execution_transition(
        developer_id=developer_id,
        execution_id=execution.id,
        data=CreateTransitionRequest(
            type="step",
            output={},
            current={"workflow": "main", "step": 0},
            next={"workflow": "wf1", "step": 1},
        ),
        client=client,
    )

    yield transition

    client.run(
        f"""
    ?[transition_id] <- ["{str(transition.id)}"]
    :delete transitions {{ transition_id  }}
    """
    )


@fixture(scope="global")
def test_tool(
    client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
):
    function = {
        "description": "A function that prints hello world",
        "parameters": {"type": "object", "properties": {}},
    }

    tool = {
        "function": function,
        "name": "hello_world1",
        "type": "function",
    }

    [tool, *_] = create_tools(
        developer_id=developer_id,
        agent_id=agent.id,
        data=[CreateToolRequest(**tool)],
        client=client,
    )

    yield tool

    delete_tool(
        developer_id=developer_id,
        agent_id=agent.id,
        tool_id=tool.id,
        client=client,
    )


@fixture(scope="global")
def client(cozo_client=cozo_client):
    client = TestClient(app=app)
    app.state.cozo_client = cozo_client

    return client


@fixture(scope="global")
def make_request(client=client, developer_id=test_developer_id):
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
