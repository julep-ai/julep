# import uuid

# from julep.api import (
#     ChatMlMessage,
#     ChatResponse,
#     ChatSettingsResponseFormat,
#     ChatSettingsResponseFormatType,
#     InputChatMlMessage,
#     InputChatMlMessageRole,
#     ResourceCreatedResponse,
#     ResourceUpdatedResponse,
#     Session,
#     Suggestion,
#     Tool,
#     ToolChoiceOption,
# )
# from julep.api.core import ApiError
# from ward import test

# from tests.fixtures import agent, async_client, client, session, user


# @test("get existing session")
# def _(existing_session=session, client=client):
#     response = client.sessions.get(id=existing_session.id)

#     assert isinstance(response, Session)
#     assert response.id == existing_session.id


# @test("async get existing sessions")
# async def _(existing_session=session, client=async_client):
#     response = await client.sessions.get(id=existing_session.id)

#     assert isinstance(response, Session)
#     assert response.id == existing_session.id


# @test("get non-existing session")
# def _(client=client):
#     try:
#         client.sessions.get(id=uuid.uuid4())
#     except ApiError as e:
#         assert e.status_code == 404
#     except Exception:
#         assert False
#     else:
#         assert False


# @test("async get non-existing sessions")
# async def _(existing_session=session, client=async_client):
#     try:
#         await client.sessions.get(id=uuid.uuid4())
#     except ApiError as e:
#         assert e.status_code == 404
#     except Exception:
#         assert False
#     else:
#         assert False


# @test("create sessions")
# def _(user=user, agent=agent, client=client):
#     response = client.sessions.create(
#         user_id=user.id,
#         agent_id=agent.id,
#         situation="test situation",
#     )

#     assert isinstance(response, ResourceCreatedResponse)
#     assert response.created_at
#     bool(uuid.UUID(str(response.id), version=4))


# @test("async create sessions")
# async def _(user=user, agent=agent, client=async_client):
#     response = await client.sessions.create(
#         user_id=user.id,
#         agent_id=agent.id,
#         situation="test situation",
#     )

#     assert isinstance(response, ResourceCreatedResponse)
#     assert response.created_at
#     bool(uuid.UUID(str(response.id), version=4))


# @test("list sessions")
# def _(existing_session=session, client=client):
#     response = client.sessions.list()

#     assert len(response) > 0
#     assert isinstance(response[0], Session)
#     assert response[0].id == existing_session.id


# @test("async list sessions")
# async def _(existing_session=session, client=async_client):
#     response = await client.sessions.list()

#     assert len(response) > 0
#     assert isinstance(response[0], Session)
#     assert response[0].id == existing_session.id


# @test("update existing session")
# def _(existing_session=session, client=client):
#     response = client.sessions.update(
#         session_id=existing_session.id,
#         situation="test situation",
#     )

#     assert isinstance(response, ResourceUpdatedResponse)
#     assert response.updated_at
#     assert response.updated_at != existing_session.updated_at
#     assert response.id == existing_session.id


# @test("async update existing session")
# async def _(existing_session=session, client=async_client):
#     response = await client.sessions.update(
#         session_id=existing_session.id,
#         situation="test situation",
#     )

#     assert isinstance(response, ResourceUpdatedResponse)
#     assert response.updated_at
#     assert response.updated_at != existing_session.updated_at
#     assert response.id == existing_session.id


# @test("update non-existing session")
# def _(client=client):
#     try:
#         client.sessions.update(
#             session_id=uuid.uuid4(),
#             situation="test situation",
#         )
#     except ApiError as e:
#         assert e.status_code == 404
#     except Exception:
#         assert False
#     else:
#         assert False


# @test("async update non-existing session")
# async def _(client=async_client):
#     try:
#         await client.sessions.update(
#             session_id=uuid.uuid4(),
#             situation="test situation",
#         )
#     except ApiError as e:
#         assert e.status_code == 404
#     except Exception:
#         assert False
#     else:
#         assert False


# @test("delete existing sessions")
# def _(existing_session=session, client=client):
#     response = client.sessions.delete(
#         session_id=existing_session.id,
#     )

#     assert response is None


# @test("async delete existing sessions")
# async def _(existing_session=session, client=client):
#     response = await client.sessions.delete(
#         session_id=existing_session.id,
#     )

#     assert response is None


# # TODO: implement below tests properly
# @test("sessions.chat")
# def _(client=client):
#     response = client.sessions.chat(
#         session_id=str(uuid.uuid4()),
#         messages=[
#             InputChatMlMessage(
#                 role=InputChatMlMessageRole.USER,
#                 content="test content",
#                 name="tets name",
#             )
#         ],
#         tools=[
#             Tool(
#                 **{
#                     "type": "function",
#                     "function": {
#                         "description": "test description",
#                         "name": "test name",
#                         "parameters": {"test_arg": "test val"},
#                     },
#                     "id": str(uuid.uuid4()),
#                 },
#             )
#         ],
#         tool_choice=ToolChoiceOption("auto"),
#         frequency_penalty=0.5,
#         length_penalty=0.5,
#         logit_bias={"test": 1},
#         max_tokens=120,
#         presence_penalty=0.5,
#         repetition_penalty=0.5,
#         response_format=ChatSettingsResponseFormat(
#             type=ChatSettingsResponseFormatType.TEXT,
#         ),
#         seed=1,
#         stop=["<"],
#         stream=False,
#         temperature=0.7,
#         top_p=0.9,
#         recall=False,
#         remember=False,
#     )

#     assert isinstance(response, ChatResponse)


# @test("async sessions.chat")
# async def _(client=async_client):
#     response = await client.sessions.chat(
#         session_id=str(uuid.uuid4()),
#         messages=[
#             InputChatMlMessage(
#                 role=InputChatMlMessageRole.USER,
#                 content="test content",
#                 name="tets name",
#             )
#         ],
#         tools=[
#             Tool(
#                 **{
#                     "type": "function",
#                     "function": {
#                         "description": "test description",
#                         "name": "test name",
#                         "parameters": {"test_arg": "test val"},
#                     },
#                     "id": str(uuid.uuid4()),
#                 },
#             )
#         ],
#         tool_choice=ToolChoiceOption("auto"),
#         frequency_penalty=0.5,
#         length_penalty=0.5,
#         logit_bias={"test": 1},
#         max_tokens=120,
#         presence_penalty=0.5,
#         repetition_penalty=0.5,
#         response_format=ChatSettingsResponseFormat(
#             type=ChatSettingsResponseFormatType.TEXT,
#         ),
#         seed=1,
#         stop=["<"],
#         stream=False,
#         temperature=0.7,
#         top_p=0.9,
#         recall=False,
#         remember=False,
#     )

#     assert isinstance(response, ChatResponse)


# @test("sessions.suggestions")
# def _(client=client):
#     response = client.sessions.suggestions(
#         session_id=uuid.uuid4(),
#     )
#     assert len(response) > 0
#     assert isinstance(response[0], Suggestion)


# @test("async sessions.suggestions")
# async def _(client=async_client):
#     response = await client.sessions.suggestions(
#         session_id=uuid.uuid4(),
#     )
#     assert len(response) > 0
#     assert isinstance(response[0], Suggestion)


# @test("sessions.history")
# def _(client=client):
#     response = client.sessions.history(
#         session_id=uuid.uuid4(),
#     )
#     assert len(response) > 0
#     assert isinstance(response[0], ChatMlMessage)


# @test("async sessions.list")
# async def _(client=async_client):
#     response = await client.sessions.history(
#         session_id=uuid.uuid4(),
#     )
#     assert len(response) > 0
#     assert isinstance(response[0], ChatMlMessage)
