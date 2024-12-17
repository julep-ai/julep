# # Tests for agent queries

# from uuid_extensions import uuid7
# from ward import raises, test

# from agents_api.autogen.openapi_model import (
#     Agent,
#     CreateAgentRequest,
#     CreateOrUpdateAgentRequest,
#     PatchAgentRequest,
#     ResourceUpdatedResponse,
#     UpdateAgentRequest,
# )
# from agents_api.queries.agent.create_agent import create_agent
# from agents_api.queries.agent.create_or_update_agent import create_or_update_agent
# from agents_api.queries.agent.delete_agent import delete_agent
# from agents_api.queries.agent.get_agent import get_agent
# from agents_api.queries.agent.list_agents import list_agents
# from agents_api.queries.agent.patch_agent import patch_agent
# from agents_api.queries.agent.update_agent import update_agent
# from tests.fixtures import cozo_client, test_agent, test_developer_id


# @test("query: create agent")
# def _(client=cozo_client, developer_id=test_developer_id):
#     create_agent(
#         developer_id=developer_id,
#         data=CreateAgentRequest(
#             name="test agent",
#             about="test agent about",
#             model="gpt-4o-mini",
#         ),
#         client=client,
#     )


# @test("query: create agent with instructions")
# def _(client=cozo_client, developer_id=test_developer_id):
#     create_agent(
#         developer_id=developer_id,
#         data=CreateAgentRequest(
#             name="test agent",
#             about="test agent about",
#             model="gpt-4o-mini",
#             instructions=["test instruction"],
#         ),
#         client=client,
#     )


# @test("query: create or update agent")
# def _(client=cozo_client, developer_id=test_developer_id):
#     create_or_update_agent(
#         developer_id=developer_id,
#         agent_id=uuid7(),
#         data=CreateOrUpdateAgentRequest(
#             name="test agent",
#             about="test agent about",
#             model="gpt-4o-mini",
#             instructions=["test instruction"],
#         ),
#         client=client,
#     )


# @test("query: get agent not exists")
# def _(client=cozo_client, developer_id=test_developer_id):
#     agent_id = uuid7()

#     with raises(Exception):
#         get_agent(agent_id=agent_id, developer_id=developer_id, client=client)


# @test("query: get agent exists")
# def _(client=cozo_client, developer_id=test_developer_id, agent=test_agent):
#     result = get_agent(agent_id=agent.id, developer_id=developer_id, client=client)

#     assert result is not None
#     assert isinstance(result, Agent)


# @test("query: delete agent")
# def _(client=cozo_client, developer_id=test_developer_id):
#     temp_agent = create_agent(
#         developer_id=developer_id,
#         data=CreateAgentRequest(
#             name="test agent",
#             about="test agent about",
#             model="gpt-4o-mini",
#             instructions=["test instruction"],
#         ),
#         client=client,
#     )

#     # Delete the agent
#     delete_agent(agent_id=temp_agent.id, developer_id=developer_id, client=client)

#     # Check that the agent is deleted
#     with raises(Exception):
#         get_agent(agent_id=temp_agent.id, developer_id=developer_id, client=client)


# @test("query: update agent")
# def _(client=cozo_client, developer_id=test_developer_id, agent=test_agent):
#     result = update_agent(
#         agent_id=agent.id,
#         developer_id=developer_id,
#         data=UpdateAgentRequest(
#             name="updated agent",
#             about="updated agent about",
#             model="gpt-4o-mini",
#             default_settings={"temperature": 1.0},
#             metadata={"hello": "world"},
#         ),
#         client=client,
#     )

#     assert result is not None
#     assert isinstance(result, ResourceUpdatedResponse)

#     agent = get_agent(
#         agent_id=agent.id,
#         developer_id=developer_id,
#         client=client,
#     )

#     assert "test" not in agent.metadata


# @test("query: patch agent")
# def _(client=cozo_client, developer_id=test_developer_id, agent=test_agent):
#     result = patch_agent(
#         agent_id=agent.id,
#         developer_id=developer_id,
#         data=PatchAgentRequest(
#             name="patched agent",
#             about="patched agent about",
#             default_settings={"temperature": 1.0},
#             metadata={"something": "else"},
#         ),
#         client=client,
#     )

#     assert result is not None
#     assert isinstance(result, ResourceUpdatedResponse)

#     agent = get_agent(
#         agent_id=agent.id,
#         developer_id=developer_id,
#         client=client,
#     )

#     assert "hello" in agent.metadata


# @test("query: list agents")
# def _(client=cozo_client, developer_id=test_developer_id, agent=test_agent):
#     """Tests listing all agents associated with a developer in the database. Verifies that the correct list of agents is retrieved."""

#     result = list_agents(developer_id=developer_id, client=client)

#     assert isinstance(result, list)
#     assert all(isinstance(agent, Agent) for agent in result)
