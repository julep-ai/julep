from uuid import uuid4

from ward import raises, test

from agents_api.autogen.openapi_model import (
    Agent,
    CreateAgentRequest,
    CreateOrUpdateAgentRequest,
    PatchAgentRequest,
    ResourceUpdatedResponse,
    UpdateAgentRequest,
)
from agents_api.models.agent.create_agent import create_agent
from agents_api.models.agent.create_or_update_agent import create_or_update_agent
from agents_api.models.agent.delete_agent import delete_agent
from agents_api.models.agent.get_agent import get_agent
from agents_api.models.agent.list_agents import list_agents
from agents_api.models.agent.patch_agent import patch_agent
from agents_api.models.agent.update_agent import update_agent
from tests.fixtures import cozo_client, test_agent, test_developer_id


@test("model: create agent")
def _(client=cozo_client, developer_id=test_developer_id):
    create_agent(
        developer_id=developer_id,
        data=CreateAgentRequest(
            name="test agent",
            about="test agent about",
            model="gpt-4o-mini",
        ),
        client=client,
    )

    # FEEDBACK[@Bhabuk10]: Consider adding an assertion after the agent creation to verify that the agent was actually created and persisted in the database. This would improve test coverage.


@test("model: create agent with instructions")
def _(client=cozo_client, developer_id=test_developer_id):
    create_agent(
        developer_id=developer_id,
        data=CreateAgentRequest(
            name="test agent",
            about="test agent about",
            model="gpt-4o-mini",
            instructions=["test instruction"],
        ),
        client=client,
    )

    # FEEDBACK[@Bhabuk10]: As with the previous test, it would be beneficial to add an assertion here to validate that the agent with instructions has been created correctly. Testing the `instructions` field would ensure it's properly handled.


@test("model: create or update agent")
def _(client=cozo_client, developer_id=test_developer_id):
    create_or_update_agent(
        developer_id=developer_id,
        agent_id=uuid4(),
        data=CreateOrUpdateAgentRequest(
            name="test agent",
            about="test agent about",
            model="gpt-4o-mini",
            instructions=["test instruction"],
        ),
        client=client,
    )

    # QUESTION[@Bhabuk10]: What is the expected behavior if an agent with the given `agent_id` already exists? Should it update the existing agent or throw an error? It might be worth testing both cases to ensure that the function works correctly in both scenarios.


@test("model: get agent not exists")
def _(client=cozo_client, developer_id=test_developer_id):
    agent_id = uuid4()

    with raises(Exception):
        get_agent(agent_id=agent_id, developer_id=developer_id, client=client)

    # FEEDBACK[@Bhabuk10]: Good use of `raises(Exception)` to test the absence of an agent. It might help to make the exception more specific (if possible) to avoid catching unintended exceptions.


@test("model: get agent exists")
def _(client=cozo_client, developer_id=test_developer_id, agent=test_agent):
    result = get_agent(agent_id=agent.id, developer_id=developer_id, client=client)

    assert result is not None
    assert isinstance(result, Agent)

    # FEEDBACK[@Bhabuk10]: You could also add assertions that check the specific values in the `Agent` object to ensure that the data is being fetched correctly.


@test("model: delete agent")
def _(client=cozo_client, developer_id=test_developer_id):
    temp_agent = create_agent(
        developer_id=developer_id,
        data=CreateAgentRequest(
            name="test agent",
            about="test agent about",
            model="gpt-4o-mini",
            instructions=["test instruction"],
        ),
        client=client,
    )

    # Delete the agent
    delete_agent(agent_id=temp_agent.id, developer_id=developer_id, client=client)

    # Check that the agent is deleted
    with raises(Exception):
        get_agent(agent_id=temp_agent.id, developer_id=developer_id, client=client)

    # QUESTION[@Bhabuk10]: What happens if you try to delete an agent that doesn't exist? Should this raise an exception, or is there a different expected behavior? Consider testing that scenario as well.


@test("model: update agent")
def _(client=cozo_client, developer_id=test_developer_id, agent=test_agent):
    result = update_agent(
        agent_id=agent.id,
        developer_id=developer_id,
        data=UpdateAgentRequest(
            name="updated agent",
            about="updated agent about",
            model="gpt-4o-mini",
            default_settings={"temperature": 1.0},
            metadata={"hello": "world"},
        ),
        client=client,
    )

    assert result is not None
    assert isinstance(result, ResourceUpdatedResponse)

    agent = get_agent(
        agent_id=agent.id,
        developer_id=developer_id,
        client=client,
    )

    assert "test" not in agent.metadata


@test("model: patch agent")
def _(client=cozo_client, developer_id=test_developer_id, agent=test_agent):
    result = patch_agent(
        agent_id=agent.id,
        developer_id=developer_id,
        data=PatchAgentRequest(
            name="patched agent",
            about="patched agent about",
            default_settings={"temperature": 1.0},
            metadata={"something": "else"},
        ),
        client=client,
    )

    assert result is not None
    assert isinstance(result, ResourceUpdatedResponse)

    agent = get_agent(
        agent_id=agent.id,
        developer_id=developer_id,
        client=client,
    )

    assert "hello" in agent.metadata

    # QUESTION[@Bhabuk10]: Does patching overwrite or merge existing fields? It might be helpful to add a test case that ensures the correct behavior when patching fields that already exist in the agent.


@test("model: list agents")
def _(client=cozo_client, developer_id=test_developer_id, agent=test_agent):
    """Tests listing all agents associated with a developer in the database. Verifies that the correct list of agents is retrieved."""

    result = list_agents(developer_id=developer_id, client=client)

    assert isinstance(result, list)
    assert all(isinstance(agent, Agent) for agent in result)
