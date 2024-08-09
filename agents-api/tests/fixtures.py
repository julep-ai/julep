from uuid import uuid4

from cozo_migrate.api import apply, init
from julep import AsyncClient, Client
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
    CreateUserRequest,
)
from agents_api.models.agent.create_agent import create_agent
from agents_api.models.agent.delete_agent import delete_agent
from agents_api.models.docs.create_doc import create_doc
from agents_api.models.docs.delete_doc import delete_doc
from agents_api.models.execution.create_execution import create_execution
from agents_api.models.session.create_session import create_session
from agents_api.models.session.delete_session import delete_session
from agents_api.models.task.create_task import create_task
from agents_api.models.task.delete_task import delete_task
from agents_api.models.tools.create_tools import create_tools
from agents_api.models.tools.delete_tool import delete_tool
from agents_api.models.user.create_user import create_user
from agents_api.models.user.delete_user import delete_user

# TODO: make clients connect to real service


@fixture(scope="global")
def client():
    # Mock server base url
    base_url = "http://localhost:8080"
    client = Client(api_key="thisisnotarealapikey", base_url=base_url)

    return client


@fixture
def async_client():
    # Mock server base url
    base_url = "http://localhost:8080"
    client = AsyncClient(api_key="thisisnotarealapikey", base_url=base_url)

    return client


@fixture(scope="global")
def cozo_client(migrations_dir: str = "./migrations"):
    # Create a new client for each test
    # and initialize the schema.
    client = CozoClient()

    init(client)
    apply(client, migrations_dir=migrations_dir, all_=True)

    return client


@fixture(scope="global")
def test_developer_id(cozo_client=cozo_client):
    developer_id = uuid4()

    cozo_client.run(
        f"""
    ?[developer_id, email] <- [["{str(developer_id)}", "developers@julep.ai"]]
    :insert developers {{ developer_id, email }}
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
def test_agent(cozo_client=cozo_client, developer_id=test_developer_id):
    agent = create_agent(
        developer_id=developer_id,
        data=CreateAgentRequest(
            model="gpt-4o",
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

    yield doc

    delete_doc(
        developer_id=developer_id,
        doc_id=doc.id,
        owner_type="agent",
        owner_id=agent.id,
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
                "main": [],
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
        workflow_handle=workflow_handle,
        client=client,
    )

    yield execution

    client.run(f"""
    ?[execution_id] <- ["{str(execution.id)}"]
    :delete executions {{ execution_id  }}
    """)


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
