# # Tests for agent queries
# from uuid import uuid4

# from cozo_migrate.api import init, apply
# from pycozo import Client
# from ward import test

# from .create_agent import create_agent_query
# from .delete_agent import delete_agent_query
# from .get_agent import get_agent_query
# from .list_agents import list_agents_query
# from .update_agent import update_agent_query

# MODEL = "julep-ai/samantha-1-turbo"


# def cozo_client(migrations_dir: str = "./migrations"):
#     # Create a new client for each test
#     # and initialize the schema.
#     client = Client()

#     init(client)
#     apply(client, migrations_dir=migrations_dir, all_=True)

#     return client


# @test("model: create agent")
# def _():
#     client = cozo_client()
#     agent_id = uuid4()
#     developer_id = uuid4()

#     create_agent_query(
#         agent_id=agent_id,
#         model=MODEL,
#         developer_id=developer_id,
#         name="test agent",
#         about="test agent about",
#         client=client,
#     )


# @test("model: create agent with instructions")
# def _():
#     client = cozo_client()
#     agent_id = uuid4()
#     developer_id = uuid4()

#     create_agent_query(
#         agent_id=agent_id,
#         model=MODEL,
#         developer_id=developer_id,
#         name="test agent",
#         about="test agent about",
#         instructions=[
#             "test instruction",
#         ],
#         client=client,
#     )


# @test("model: get agent not exists")
# def _():
#     client = cozo_client()
#     agent_id = uuid4()
#     developer_id = uuid4()

#     result = get_agent_query(
#         agent_id=agent_id, developer_id=developer_id, client=client
#     )

#     assert len(result["id"]) == 0


# @test("model: get agent exists")
# def _():
#     client = cozo_client()
#     agent_id = uuid4()
#     developer_id = uuid4()

#     result = create_agent_query(
#         agent_id=agent_id,
#         model=MODEL,
#         developer_id=developer_id,
#         name="test agent",
#         about="test agent about",
#         default_settings={"temperature": 1.5},
#         client=client,
#     )

#     result = get_agent_query(
#         agent_id=agent_id, developer_id=developer_id, client=client
#     )

#     assert len(result["id"]) == 1
#     assert "temperature" in result["default_settings"][0]
#     assert result["default_settings"][0]["temperature"] == 1.5


# @test("model: delete agent")
# def _():
#     client = cozo_client()
#     agent_id = uuid4()
#     developer_id = uuid4()

#     # Create the agent
#     result = create_agent_query(
#         agent_id=agent_id,
#         model=MODEL,
#         developer_id=developer_id,
#         name="test agent",
#         about="test agent about",
#         client=client,
#     )

#     # Delete the agent
#     result = delete_agent_query(
#         agent_id=agent_id, developer_id=developer_id, client=client
#     )

#     # Check that the agent is deleted
#     result = get_agent_query(
#         agent_id=agent_id, developer_id=developer_id, client=client
#     )

#     assert len(result["id"]) == 0


# @test("model: update agent")
# def _():
#     client = cozo_client()
#     agent_id = uuid4()
#     developer_id = uuid4()

#     create_agent_query(
#         agent_id=agent_id,
#         model=MODEL,
#         developer_id=developer_id,
#         name="test agent",
#         about="test agent about",
#         client=client,
#     )

#     result = update_agent_query(
#         agent_id=agent_id,
#         developer_id=developer_id,
#         name="updated agent",
#         about="updated agent about",
#         default_settings={"temperature": 1.5},
#         client=client,
#     )

#     data = result.iloc[0].to_dict()

#     assert data["updated_at"] > data["created_at"]


# @test("model: list agents")
# def _():
#     """Tests listing all agents associated with a developer in the database. Verifies that the correct list of agents is retrieved."""
#     client = cozo_client()
#     developer_id = uuid4()

#     result = list_agents_query(developer_id=developer_id, client=client)

#     assert len(result["id"]) == 0
