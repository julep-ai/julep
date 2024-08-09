# import uuid

# from julep.api import Agent, ResourceCreatedResponse, ResourceUpdatedResponse
# from julep.api.core import ApiError
# from ward import test

# from tests.fixtures import agent, async_client, client


# @test("create new agent with tools")
# def _(client=client):
#     agent = client.agents.create(
#         name="Samantha",
#         about="about Samantha",
#         instructions=[
#             "non-important content",
#             "important content",
#         ],
#         tools=[
#             {
#                 "type": "function",
#                 "function": {
#                     "description": "func desc",
#                     "name": "some_func",
#                     "parameters": {"param1": "string"},
#                 },
#             }
#         ],
#         default_settings={
#             "frequency_penalty": 0.1,
#             "length_penalty": 0.9,
#             "presence_penalty": 0.8,
#             "repetition_penalty": 0.7,
#             "temperature": 0.6,
#             "top_p": 0.5,
#         },
#         model="julep-ai/samantha-1-turbo",
#         docs=[
#             {
#                 "title": "some titie",
#                 "content": "some content",
#             },
#         ],
#     )

#     assert isinstance(agent, ResourceCreatedResponse)
#     assert agent.created_at
#     assert bool(uuid.UUID(str(agent.id), version=4))


# @test("async create new agent with tools")
# async def _(client=async_client):
#     agent = await client.agents.create(
#         name="Samantha",
#         about="about Samantha",
#         instructions=[
#             "non-important content",
#             "important content",
#         ],
#         tools=[
#             {
#                 "type": "function",
#                 "function": {
#                     "description": "func desc",
#                     "name": "some_func",
#                     "parameters": {"param1": "string"},
#                 },
#             }
#         ],
#         default_settings={
#             "frequency_penalty": 0.1,
#             "length_penalty": 0.9,
#             "presence_penalty": 0.8,
#             "repetition_penalty": 0.7,
#             "temperature": 0.6,
#             "top_p": 0.5,
#         },
#         model="julep-ai/samantha-1-turbo",
#         docs=[
#             {
#                 "title": "some titie",
#                 "content": "some content",
#             },
#         ],
#     )

#     assert isinstance(agent, ResourceCreatedResponse)
#     assert agent.created_at
#     assert bool(uuid.UUID(str(agent.id), version=4))


# @test("create new agent with functions")
# def _(client=client):
#     agent = client.agents.create(
#         name="Samantha",
#         about="about Samantha",
#         instructions=[
#             "non-important content",
#             "important content",
#         ],
#         functions=[
#             {
#                 "description": "func desc",
#                 "name": "some_func",
#                 "parameters": {"param1": "string"},
#             }
#         ],
#         default_settings={
#             "frequency_penalty": 0.1,
#             "length_penalty": 0.9,
#             "presence_penalty": 0.8,
#             "repetition_penalty": 0.7,
#             "temperature": 0.6,
#             "top_p": 0.5,
#         },
#         model="julep-ai/samantha-1-turbo",
#         docs=[
#             {
#                 "title": "some titie",
#                 "content": "some content",
#             },
#         ],
#     )

#     assert isinstance(agent, ResourceCreatedResponse)
#     assert agent.created_at
#     assert bool(uuid.UUID(str(agent.id), version=4))


# @test("async create new agent with functions")
# async def _(client=async_client):
#     agent = await client.agents.create(
#         name="Samantha",
#         about="about Samantha",
#         instructions=[
#             "non-important content",
#             "important content",
#         ],
#         functions=[
#             {
#                 "description": "func desc",
#                 "name": "some_func",
#                 "parameters": {"param1": "string"},
#             }
#         ],
#         default_settings={
#             "frequency_penalty": 0.1,
#             "length_penalty": 0.9,
#             "presence_penalty": 0.8,
#             "repetition_penalty": 0.7,
#             "temperature": 0.6,
#             "top_p": 0.5,
#         },
#         model="julep-ai/samantha-1-turbo",
#         docs=[
#             {
#                 "title": "some titie",
#                 "content": "some content",
#             },
#         ],
#     )

#     assert isinstance(agent, ResourceCreatedResponse)
#     assert agent.created_at
#     assert bool(uuid.UUID(str(agent.id), version=4))


# @test("create new agent with functions and tools")
# def _(client=client):
#     try:
#         client.agents.create(
#             name="Samantha",
#             about="about Samantha",
#             instructions=[
#                 "non-important content",
#                 "important content",
#             ],
#             tools=[
#                 {
#                     "type": "function",
#                     "function": {
#                         "description": "func desc",
#                         "name": "some_func",
#                         "parameters": {"param1": "string"},
#                     },
#                 }
#             ],
#             functions=[
#                 {
#                     "description": "func desc",
#                     "name": "some_func",
#                     "parameters": {"param1": "string"},
#                 }
#             ],
#             default_settings={
#                 "frequency_penalty": 0.1,
#                 "length_penalty": 0.9,
#                 "presence_penalty": 0.8,
#                 "repetition_penalty": 0.7,
#                 "temperature": 0.6,
#                 "top_p": 0.5,
#             },
#             model="julep-ai/samantha-1-turbo",
#             docs=[
#                 {
#                     "title": "some titie",
#                     "content": "some content",
#                 },
#             ],
#         )
#     except Exception:
#         assert True
#     else:
#         assert False


# @test("async create new agent with functions and tools")
# async def _(client=async_client):
#     try:
#         await client.agents.create(
#             name="Samantha",
#             about="about Samantha",
#             instructions=[
#                 "non-important content",
#                 "important content",
#             ],
#             tools=[
#                 {
#                     "type": "function",
#                     "function": {
#                         "description": "func desc",
#                         "name": "some_func",
#                         "parameters": {"param1": "string"},
#                     },
#                 }
#             ],
#             functions=[
#                 {
#                     "description": "func desc",
#                     "name": "some_func",
#                     "parameters": {"param1": "string"},
#                 }
#             ],
#             default_settings={
#                 "frequency_penalty": 0.1,
#                 "length_penalty": 0.9,
#                 "presence_penalty": 0.8,
#                 "repetition_penalty": 0.7,
#                 "temperature": 0.6,
#                 "top_p": 0.5,
#             },
#             model="julep-ai/samantha-1-turbo",
#             docs=[
#                 {
#                     "title": "some titie",
#                     "content": "some content",
#                 },
#             ],
#         )
#     except Exception:
#         assert True
#     else:
#         assert False


# @test("update existing agent")
# def _(client=client, existing_agent=agent):
#     response = client.agents.update(
#         agent_id=agent.id,
#         name="test user",
#         about="test user about",
#         instructions=["test agent instructions"],
#         default_settings={"temperature": 0.5},
#         model="some model",
#     )

#     assert isinstance(response, ResourceUpdatedResponse)
#     assert response.updated_at != existing_agent.updated_at
#     assert response.id == existing_agent.id


# @test("async update existing agent")
# async def _(client=async_client, existing_agent=agent):
#     response = await client.agents.update(
#         agent_id=agent.id,
#         name="test user",
#         about="test user about",
#         instructions=["test agent instructions"],
#         default_settings={"temperature": 0.5},
#         model="some model",
#     )

#     assert isinstance(response, ResourceUpdatedResponse)
#     assert response.updated_at != existing_agent.updated_at
#     assert response.id == existing_agent.id


# @test("update non-existing agent")
# def _(client=client):
#     try:
#         client.agents.update(
#             agent_id=uuid.uuid4(),
#             name="test user",
#             about="test user about",
#             instructions=["test agent instructions"],
#             default_settings={"temperature": 0.5},
#             model="some model",
#         )
#     except ApiError as e:
#         assert e.status_code == 404
#     except Exception:
#         assert False
#     else:
#         assert False


# @test("async update non-existing agent")
# async def _(client=async_client):
#     try:
#         await client.agents.update(
#             agent_id=uuid.uuid4(),
#             name="test user",
#             about="test user about",
#             instructions=["test agent instructions"],
#             default_settings={"temperature": 0.5},
#             model="some model",
#         )
#     except ApiError as e:
#         assert e.status_code == 404
#     except Exception:
#         assert False
#     else:
#         assert False


# @test("delete existing agent")
# def _(client=client, existing_agent=agent):
#     response = client.agents.delete(
#         existing_agent.id,
#     )

#     assert response is None


# @test("async delete existing agent")
# async def _(client=async_client, existing_agent=agent):
#     response = await client.agents.delete(
#         existing_agent.id,
#     )

#     assert response is None


# @test("delete non-existing agent")
# def _(client=client):
#     try:
#         client.agents.delete(
#             uuid.uuid4(),
#         )
#     except ApiError as e:
#         assert e.status_code == 404
#     except Exception:
#         assert False
#     else:
#         assert False


# @test("async delete non-existing agent")
# async def _(client=async_client):
#     try:
#         await client.agents.delete(
#             uuid.uuid4(),
#         )
#     except ApiError as e:
#         assert e.status_code == 404
#     except Exception:
#         assert False
#     else:
#         assert False


# @test("get existing agent")
# def _(client=client, existing_agent=agent):
#     response = client.agents.get(existing_agent.id)
#     assert isinstance(response, Agent)
#     assert response.id == existing_agent.id


# @test("async get existing agent")
# async def _(client=async_client, existing_agent=agent):
#     response = await client.agents.get(existing_agent.id)
#     assert isinstance(response, Agent)
#     assert response.id == existing_agent.id


# @test("get non-existing agent")
# def _(client=client):
#     try:
#         client.agents.get(uuid.uuid4())
#     except ApiError as e:
#         assert e.status_code == 404
#     except Exception:
#         assert False
#     else:
#         assert False


# @test("async get non-existing agent")
# async def _(client=async_client):
#     try:
#         await client.agents.get(uuid.uuid4())
#     except ApiError as e:
#         assert e.status_code == 404
#     except Exception:
#         assert False
#     else:
#         assert False


# @test("list agents")
# def _(client=client, existing_agent=agent):
#     response = client.agents.list()
#     assert len(response) > 0
#     assert isinstance(response[0], Agent)
#     assert response[0].id == existing_agent.id


# @test("async list agents")
# async def _(client=async_client, existing_agent=agent):
#     response = await client.agents.list()
#     assert len(response) > 0
#     assert isinstance(response[0], Agent)
#     assert response[0].id == existing_agent.id
