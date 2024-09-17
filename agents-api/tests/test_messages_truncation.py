# from uuid import uuid4

# from ward import raises, test

# from agents_api.autogen.openapi_model import Role
# from agents_api.common.protocol.entries import Entry
# from agents_api.routers.sessions.exceptions import InputTooBigError
# from tests.fixtures import base_session


# @test("truncate empty messages list", tags=["messages_truncate"])
# def _(session=base_session):
#     messages: list[Entry] = []
#     result = session.truncate(messages, 10)

#     assert messages == result


# @test("do not truncate", tags=["messages_truncate"])
# def _(session=base_session):
#     contents = [
#         "content1",
#         "content2",
#         "content3",
#     ]
#     threshold = sum([len(c) // 3.5 for c in contents])

#     messages: list[Entry] = [
#         Entry(session_id=uuid4(), role=Role.user, content=contents[0][0]),
#         Entry(session_id=uuid4(), role=Role.assistant, content=contents[1][0]),
#         Entry(session_id=uuid4(), role=Role.user, content=contents[2][0]),
#     ]
#     result = session.truncate(messages, threshold)

#     assert messages == result


# @test("truncate thoughts partially", tags=["messages_truncate"])
# def _(session=base_session):
#     contents = [
#         ("content1", True),
#         ("content2", True),
#         ("content3", False),
#         ("content4", True),
#         ("content5", True),
#         ("content6", True),
#     ]
#     session_ids = [uuid4()] * len(contents)
#     threshold = sum([len(c) // 3.5 for c, i in contents if i])

#     messages: list[Entry] = [
#         Entry(
#             session_id=session_ids[0],
#             role=Role.system,
#             name="thought",
#             content=contents[0][0],
#         ),
#         Entry(session_id=session_ids[1], role=Role.assistant, content=contents[1][0]),
#         Entry(
#             session_id=session_ids[2],
#             role=Role.system,
#             name="thought",
#             content=contents[2][0],
#         ),
#         Entry(
#             session_id=session_ids[3],
#             role=Role.system,
#             name="thought",
#             content=contents[3][0],
#         ),
#         Entry(session_id=session_ids[4], role=Role.user, content=contents[4][0]),
#         Entry(session_id=session_ids[5], role=Role.assistant, content=contents[5][0]),
#     ]
#     result = session.truncate(messages, threshold)
#     [
#         messages[0],
#         messages[1],
#         messages[3],
#         messages[4],
#         messages[5],
#     ]

#     assert result == [
#         messages[0],
#         messages[1],
#         messages[3],
#         messages[4],
#         messages[5],
#     ]


# @test("truncate thoughts partially 2", tags=["messages_truncate"])
# def _(session=base_session):
#     contents = [
#         ("content1", True),
#         ("content2", True),
#         ("content3", False),
#         ("content4", False),
#         ("content5", True),
#         ("content6", True),
#     ]
#     session_ids = [uuid4()] * len(contents)
#     threshold = sum([len(c) // 3.5 for c, i in contents if i])

#     messages: list[Entry] = [
#         Entry(
#             session_id=session_ids[0],
#             role=Role.system,
#             name="thought",
#             content=contents[0][0],
#         ),
#         Entry(session_id=session_ids[1], role=Role.assistant, content=contents[1][0]),
#         Entry(
#             session_id=session_ids[2],
#             role=Role.system,
#             name="thought",
#             content=contents[2][0],
#         ),
#         Entry(
#             session_id=session_ids[3],
#             role=Role.system,
#             name="thought",
#             content=contents[3][0],
#         ),
#         Entry(session_id=session_ids[4], role=Role.user, content=contents[4][0]),
#         Entry(session_id=session_ids[5], role=Role.assistant, content=contents[5][0]),
#     ]
#     result = session.truncate(messages, threshold)

#     assert result == [
#         messages[0],
#         messages[1],
#         messages[4],
#         messages[5],
#     ]


# @test("truncate all thoughts", tags=["messages_truncate"])
# def _(session=base_session):
#     contents = [
#         ("content1", False),
#         ("content2", True),
#         ("content3", False),
#         ("content4", False),
#         ("content5", True),
#         ("content6", True),
#         ("content7", False),
#     ]
#     session_ids = [uuid4()] * len(contents)
#     threshold = sum([len(c) // 3.5 for c, i in contents if i])

#     messages: list[Entry] = [
#         Entry(
#             session_id=session_ids[0],
#             role=Role.system,
#             name="thought",
#             content=contents[0][0],
#         ),
#         Entry(session_id=session_ids[1], role=Role.assistant, content=contents[1][0]),
#         Entry(
#             session_id=session_ids[2],
#             role=Role.system,
#             name="thought",
#             content=contents[2][0],
#         ),
#         Entry(
#             session_id=session_ids[3],
#             role=Role.system,
#             name="thought",
#             content=contents[3][0],
#         ),
#         Entry(session_id=session_ids[4], role=Role.user, content=contents[4][0]),
#         Entry(session_id=session_ids[5], role=Role.assistant, content=contents[5][0]),
#         Entry(
#             session_id=session_ids[6],
#             role=Role.system,
#             name="thought",
#             content=contents[6][0],
#         ),
#     ]
#     result = session.truncate(messages, threshold)

#     assert result == [
#         messages[1],
#         messages[4],
#         messages[5],
#     ]


# @test("truncate user assistant pairs", tags=["messages_truncate"])
# def _(session=base_session):
#     contents = [
#         ("content1", False),
#         ("content2", True),
#         ("content3", False),
#         ("content4", False),
#         ("content5", True),
#         ("content6", True),
#         ("content7", True),
#         ("content8", False),
#         ("content9", True),
#         ("content10", True),
#         ("content11", True),
#         ("content12", True),
#         ("content13", False),
#     ]
#     session_ids = [uuid4()] * len(contents)
#     threshold = sum([len(c) // 3.5 for c, i in contents if i])

#     messages: list[Entry] = [
#         Entry(
#             session_id=session_ids[0],
#             role=Role.system,
#             name="thought",
#             content=contents[0][0],
#         ),
#         Entry(session_id=session_ids[1], role=Role.assistant, content=contents[1][0]),
#         Entry(
#             session_id=session_ids[2],
#             role=Role.system,
#             name="thought",
#             content=contents[2][0],
#         ),
#         Entry(
#             session_id=session_ids[3],
#             role=Role.system,
#             name="thought",
#             content=contents[3][0],
#         ),
#         Entry(session_id=session_ids[4], role=Role.user, content=contents[4][0]),
#         Entry(session_id=session_ids[5], role=Role.assistant, content=contents[5][0]),
#         Entry(session_id=session_ids[6], role=Role.user, content=contents[6][0]),
#         Entry(session_id=session_ids[7], role=Role.assistant, content=contents[7][0]),
#         Entry(session_id=session_ids[8], role=Role.user, content=contents[8][0]),
#         Entry(session_id=session_ids[9], role=Role.assistant, content=contents[9][0]),
#         Entry(session_id=session_ids[10], role=Role.user, content=contents[10][0]),
#         Entry(session_id=session_ids[11], role=Role.assistant, content=contents[11][0]),
#         Entry(
#             session_id=session_ids[12],
#             role=Role.system,
#             name="thought",
#             content=contents[12][0],
#         ),
#     ]

#     result = session.truncate(messages, threshold)

#     assert result == [
#         messages[1],
#         messages[4],
#         messages[5],
#         messages[6],
#         messages[8],
#         messages[9],
#         messages[10],
#         messages[11],
#     ]


# @test("unable to truncate", tags=["messages_truncate"])
# def _(session=base_session):
#     contents = [
#         ("content1", False),
#         ("content2", True),
#         ("content3", False),
#         ("content4", False),
#         ("content5", False),
#         ("content6", False),
#         ("content7", True),
#         ("content8", False),
#         ("content9", True),
#         ("content10", False),
#     ]
#     session_ids = [uuid4()] * len(contents)
#     threshold = sum([len(c) // 3.5 for c, i in contents if i])
#     all_tokens = sum([len(c) // 3.5 for c, _ in contents])

#     messages: list[Entry] = [
#         Entry(
#             session_id=session_ids[0],
#             role=Role.system,
#             name="thought",
#             content=contents[0][0],
#         ),
#         Entry(session_id=session_ids[1], role=Role.assistant, content=contents[1][0]),
#         Entry(
#             session_id=session_ids[2],
#             role=Role.system,
#             name="thought",
#             content=contents[2][0],
#         ),
#         Entry(
#             session_id=session_ids[3],
#             role=Role.system,
#             name="thought",
#             content=contents[3][0],
#         ),
#         Entry(session_id=session_ids[4], role=Role.user, content=contents[4][0]),
#         Entry(session_id=session_ids[5], role=Role.assistant, content=contents[5][0]),
#         Entry(session_id=session_ids[6], role=Role.user, content=contents[6][0]),
#         Entry(session_id=session_ids[7], role=Role.assistant, content=contents[7][0]),
#         Entry(session_id=session_ids[8], role=Role.user, content=contents[8][0]),
#         Entry(
#             session_id=session_ids[9],
#             role=Role.system,
#             name="thought",
#             content=contents[9][0],
#         ),
#     ]
#     with raises(InputTooBigError) as ex:
#         session.truncate(messages, threshold)

#     assert (
#         str(ex.raised)
#         == f"input is too big, {threshold} tokens required, but you got {all_tokens} tokens"
#     )
